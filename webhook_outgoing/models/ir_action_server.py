# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json
import logging
from contextlib import closing

import requests
from jinja2 import BaseLoader, Environment

from odoo import SUPERUSER_ID, api, fields, models, registry
from odoo.tools import ustr
from odoo.tools.safe_eval import safe_eval

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)


ESCAPE_CHARS = ['"', "\n", "\r", "\t", "\b", "\f"]
REPLACE_CHARS = ['\\"', "\\n", "\\r", "\\t", "\\b", "\\f"]

DEFAULT_GET_TIMEOUT = 5
DEFAULT_POST_TIMEOUT = 5


class ServerAction(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("custom_webhook", "Custom Webhook")],
        ondelete={"custom_webhook": "cascade"},
    )
    endpoint = fields.Char()
    headers = fields.Text(default="{}")
    body_template = fields.Text(default="{}")
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
        Prepare request params/body by rendering template and send requests.
        """
        self.ensure_one()

        if eval_context is None:
            eval_context = dict(
                self._get_eval_context(action=self),
                record=record,
                records=record,
            )

        try:
            response, body = getattr(
                self, "_execute_webhook_%s_request" % self.request_method
            )(record, eval_context)
            response.raise_for_status()
        except Exception as e:
            self._handle_exception(response, e, body)
        else:
            status_code = self._get_success_request_status_code(response)
            if status_code != 200:
                raise RetryableJobError
            self._webhook_logging(body, response)

    def _get_webhook_headers(self):
        self.ensure_one()
        headers = json.loads(self.headers.strip()).copy() if self.headers else {}
        return str(headers)

    def _prepare_data_for_post_graphql(self, template, record):
        def get_escaped_field(record, field_name):
            str_field = getattr(record, str(field_name), False)
            if str_field and isinstance(str_field, str):
                str_field = str_field.strip()
                for esc_char, rep_char in zip(ESCAPE_CHARS, REPLACE_CHARS, strict=True):
                    str_field = str_field.replace(esc_char, rep_char)
            return str_field

        query = template.render(record=record, escape=get_escaped_field)
        payload = json.dumps({"query": query, "variables": {}})
        return payload

    def _prepare_data_for_post_request(self, template, record, eval_context):
        data = template.render(**dict(eval_context, record=record))
        return data.encode(encoding="utf-8")

    def _prepare_data_for_post_slack(self, template, record, eval_context):
        data = template.render(**dict(eval_context, record=record))
        return data.encode(encoding="utf-8")

    def _prepare_data_for_get(self, template, record, eval_context):
        data = template.render(**dict(eval_context, record=record))
        return data.encode(encoding="utf-8")

    def _execute_webhook_get_request(self, record, eval_context):
        self.ensure_one()

        endpoint = self.endpoint
        headers = safe_eval(self._get_webhook_headers())
        template = Environment(loader=BaseLoader()).from_string(self.body_template)
        params = self._prepare_data_for_get(template, record, eval_context)
        r = requests.get(
            endpoint,
            params=(params or {}),
            headers=headers,
            timeout=DEFAULT_GET_TIMEOUT,
        )

        return r, params

    def _execute_webhook_post_request(self, record, eval_context):
        endpoint = self.endpoint
        headers = safe_eval(self._get_webhook_headers())
        template = Environment(loader=BaseLoader()).from_string(self.body_template)
        payload = {}

        prepare_method = "_prepare_data_for_post_%s" % self.request_type
        payload = getattr(self, prepare_method)(template, record, eval_context)

        r = requests.post(
            endpoint, data=payload, headers=headers, timeout=DEFAULT_POST_TIMEOUT
        )

        return r, payload

    def _get_success_request_status_code(self, response):
        """
        Sometimes `200` success code is just weirdly return, so we explicitly check if
        a request is success or not based on request type.
        """
        status_code = 200

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

        elif self.type == "slack":
            status_code = response.status_code

        return status_code

    def _webhook_logging(self, body, response):
        if self.log_webhook_calls:
            with closing(registry(self.env.cr.dbname).cursor()) as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                def create_log(env, response):
                    vals = {
                        "webhook_type": "outgoing",
                        "webhook": f"{self.name} ({self})",
                        "endpoint": self.endpoint,
                        "headers": self.headers,
                        "request": json.dumps(ustr(body), indent=4),
                        "response": ustr(response),
                        "status": getattr(response, "status_code", None),
                    }
                    env["webhook.logging"].create(vals)
                    env.cr.commit()

                create_log(env, response)

    def _handle_exception(self, response, exception, body):
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
            # Final exception if none above catched
            _logger.error(
                "Internal exception happened during sending webhook request",
                exc_info=True,
            )
        finally:
            self._webhook_logging(body, exception)
