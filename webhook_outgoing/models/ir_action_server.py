# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json
import logging

import requests
from jinja2 import BaseLoader, Environment

from odoo import fields, models
from odoo.tools import ustr
from odoo.tools.safe_eval import safe_eval

from ..helpers import get_escaped_value

_logger = logging.getLogger(__name__)


DEFAULT_GET_TIMEOUT = 5
DEFAULT_POST_TIMEOUT = 5

DEFAULT_BODY_TEMPLATE = """{# Available variables:
  - record: record on which the action is triggered; may be void
#}
{
    "id": {{record.id}},
    "name": "{{record.name}}"
}
"""


class IrServerAction(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("custom_webhook", "Custom Webhook")],
        ondelete={"custom_webhook": "cascade"},
    )
    endpoint = fields.Char()
    headers = fields.Text(default="{}")
    body_template = fields.Text(default=DEFAULT_BODY_TEMPLATE)
    request_method = fields.Selection(
        [
            ("get", "GET"),
            ("post", "POST"),
        ],
        default="post",
    )
    request_type = fields.Selection(
        [
            ("request", "HTTP Request"),
            ("graphql", "GraphQL"),
            ("slack", "Slack"),
        ],
        default="request",
    )
    log_webhook_calls = fields.Boolean(string="Log Calls", default=False)
    delay_execution = fields.Boolean()
    delay = fields.Integer("Delay ETA (s)", default=0)

    def _run_action_custom_webhook_multi(self, eval_context):
        """
        Execute to send webhook requests to triggered records. Note that execution
        is done on each record and not in batch.
        :param dict eval_context: context used for execution
        :return dict action: return current executed action for next execution
        """
        records = eval_context.get("records", self.model_id.browse())

        for record in records:
            if self.delay_execution:
                self.with_delay(eta=self.delay)._execute_webhook(record, None)
            else:
                self._execute_webhook(record, eval_context)

        return eval_context.get("action")

    def _execute_webhook(self, record, eval_context):
        """
        Prepare params for GET, or body for POST and send webhook request

        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        """
        self.ensure_one()

        if eval_context is None:
            eval_context = dict(
                self._get_eval_context(action=self), record=record, records=record
            )

        response = body = None
        try:
            func = getattr(self, "_execute_webhook_%s_request" % self.request_method)
            response, body = func(record, eval_context)
            response.raise_for_status()

            status_code = self._get_body_status_code(response)
            if status_code != 200:
                raise requests.exceptions.HTTPError(
                    "Received response with status code %s" % status_code
                )

        except Exception as e:
            # Try to get the body from the function if it was prepared before exception
            self._handle_exception(response, e, body)
        else:
            self._webhook_logging(body, response)

    def _execute_webhook_get_request(self, record, eval_context):
        """
        Execute outgoing webhook GET request

        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        :return response: response object after executed webhook request
        :return params: params used while sending webhook request, for logging
        """
        self.ensure_one()

        endpoint = self.endpoint
        headers = self._get_webhook_headers()
        params = self._prepare_data_for_get(record, eval_context)
        # Store params in case an exception occurs during the request
        response = requests.get(
            endpoint,
            params=(params or {}),
            headers=headers,
            timeout=DEFAULT_GET_TIMEOUT,
        )

        return response, params

    def _execute_webhook_post_request(self, record, eval_context):
        """
        Execute outgoing webhook POST request

        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        :return response: response object after executed webhook request
        :return payload: body/payload used while sending webhook request, for logging
        """
        self.ensure_one()

        endpoint = self.endpoint
        headers = self._get_webhook_headers()
        payload = {}

        prepare_method = "_prepare_data_for_post_%s" % self.request_type
        if not hasattr(self, prepare_method):
            prepare_method = "_prepare_data_for_post_request"

        payload = getattr(self, prepare_method)(record, eval_context)
        # Store payload in case an exception occurs during the request

        response = requests.post(
            endpoint, data=payload, headers=headers, timeout=DEFAULT_POST_TIMEOUT
        )

        return response, payload

    def _get_webhook_headers(self):
        """Prepare headers for outgoing webhook

        Accepts both JSON format and Python dict literals:
        - JSON: {"Authorization": "Bearer token"}
        - Python: {'Authorization': 'Bearer token'}

        :return dict headers: headers dictionary
        """
        self.ensure_one()
        headers_str = (self.headers or "").strip()
        if not headers_str:
            return {}

        try:
            # Use safe_eval to handle both JSON and Python dict literals
            headers = safe_eval(headers_str)
            if not isinstance(headers, dict):
                _logger.warning(
                    "Headers must be a dict, got %s. Returning empty dict.",
                    type(headers).__name__,
                )
                return {}
            return headers
        except Exception as e:
            _logger.error(
                "Failed to parse headers '%s': %s. Returning empty dict.",
                headers_str,
                e,
            )
            return {}

    def _prepare_data_for_get(self, record, eval_context):
        """Render template as parameters to be passed down the request
        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        :return str params: parameters object in string format
        """
        self.ensure_one()
        template = Environment(loader=BaseLoader()).from_string(self.body_template)
        data = template.render(**dict(eval_context, record=record))
        return data.encode(encoding="utf-8")

    def _prepare_data_for_post_request(self, record, eval_context):
        """Render template as body to be passed down the request
        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        :return str params: body object in string format
        """
        self.ensure_one()
        template = Environment(loader=BaseLoader()).from_string(self.body_template)
        data = template.render(**dict(eval_context, record=record))
        return data.encode(encoding="utf-8")

    def _prepare_data_for_post_graphql(self, record, eval_context):
        """Render template as body specifically for GraphQL request in form of POST
        :param record: record which action is executed upon
        :param eval_context: context used during action execution
        :return str params: body object in string format
        """
        self.ensure_one()

        template = Environment(loader=BaseLoader()).from_string(self.body_template)
        query = template.render(
            **dict(eval_context, record=record, escape=get_escaped_value)
        )
        payload = json.dumps({"query": query, "variables": {}})
        return payload

    def _get_body_status_code(self, response):
        """
        Sometimes `200` success code is just weirdly return, so we explicitly check if
        a request is success or not based on request type.
        :param response: response object from request
        :return int status_code: response status code
        """
        status_code = response.status_code

        if self.type == "graphql":
            response_data = json.loads(response.text) if response.text else False
            if (
                response_data
                and response_data.get("data")
                and isinstance(response_data.get("data"), dict)
            ):
                for __, value in response_data["data"].items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if k == "statusCode":
                                status_code = v

        return status_code

    def _webhook_logging(self, body, response):
        """Log webhook requests for troubleshooting
        :param str body: params or bodys used in webhook request
        :param response: response of webhook request or exception
        """
        if self.log_webhook_calls:
            # Handle case where response might be an exception or None
            if hasattr(response, "content"):
                response_content = ustr(response.content)
                status_code = getattr(response, "status_code", None)
            else:
                # Response is an exception or None
                response_content = ustr(response) if response else "No response"
                status_code = None

            vals = {
                "webhook_type": "outgoing",
                "webhook": "%s (%s)" % (self.name, self),
                "endpoint": self.endpoint,
                "headers": self.headers,
                "body": ustr(body),
                "response": response_content,
                "status": status_code,
            }
            self.env["webhook.logging"].create(vals)

    def _handle_exception(self, response, exception, body):
        """Hanlde exceptions while sending webhook requests
        :param response: response of webhook request
        :param exception: original exception raised while executing request
        :param str body: params or bodies used in webhook request
        """
        try:
            raise exception
        except requests.exceptions.HTTPError:
            _logger.error("HTTPError during request", exc_info=True)
        except requests.exceptions.ConnectionError:
            _logger.error("Error Connecting during request", exc_info=True)
        except requests.exceptions.Timeout:
            _logger.error("Connection Timeout", exc_info=True)
        except requests.exceptions.RequestException:
            _logger.error("Something wrong happened during request", exc_info=True)
        except Exception:
            # Final exception if none above caught
            _logger.error(
                "Internal exception happened during sending webhook request",
                exc_info=True,
            )
        finally:
            # For HTTP errors, we have a response with status code
            # For other errors (connection, timeout), we don't have a response
            if isinstance(exception, requests.exceptions.HTTPError) and response:
                self._webhook_logging(body, response)
            else:
                self._webhook_logging(body, exception)
