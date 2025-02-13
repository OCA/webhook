# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import logging
import traceback
from uuid import uuid4

from pytz import timezone

from odoo import Command, _, api, exceptions, fields, models, tools
from odoo.tools import ustr
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class InheritedBaseAutomation(models.Model):
    _inherit = "base.automation"

    trigger = fields.Selection(
        selection_add=[("on_webhook", "On webhook")], ondelete={"on_webhook": "cascade"}
    )
    webhook_uuid = fields.Char(
        string="Webhook UUID",
        readonly=True,
        copy=False,
        default=lambda self: str(uuid4()),
    )
    url = fields.Char(string="Webhook URL", compute="_compute_url")
    log_webhook_calls = fields.Boolean(string="Log Calls", default=False)
    allow_creation = fields.Boolean(
        string="Allow creation?",
        help="Allow executing webhook to maybe create record if a record is not "
        "found using record getter",
    )
    record_getter = fields.Char(
        default="model.env[payload.get('_model')].browse(int(payload.get('_id')))",
        help="This code will be run to find on which record the automation rule should be run.",
    )
    create_record_code = fields.Text(
        "Record Creation Code",
        default="""# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered;
#           is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered
#             in multi-mode; may be void
#  - payload: input payload from webhook request
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Odoo function to compare floats based on specific precisions
#  - log: log(message, level='info'): logging function to record debug information
#         in ir.logging table
#  - UserError: Warning Exception to use with raise
#  - Command: x2Many commands namespace
# You must return the created record by assign it to `record` variable:
#  - record = res.partner(1,)
""",
        help="This block of code is eval if Record Getter couldn't find a matching record.",
    )
    create_record_action_id = fields.Many2one(comodel_name="ir.actions.server")
    delay_execution = fields.Boolean(
        help="Queue actions to perform to delay execution."
    )

    @api.depends("webhook_uuid")
    def _compute_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for webhook in self:
            webhook.webhook_url = "%s/web/hook/%s" % (base_url, webhook.webhook_uuid)

    @api.depends("trigger", "webhook_uuid")
    def _compute_url(self):
        for automation in self:
            if automation.trigger != "on_webhook":
                automation.url = ""
            else:
                automation.url = "%s/web/hook/%s" % (
                    automation.get_base_url(),
                    automation.webhook_uuid,
                )

    def _get_eval_context(self, payload=None):
        """
        Override to add payload to context
        """
        eval_context = super()._get_eval_context()
        eval_context["model"] = self.env[self.model_name]
        eval_context["payload"] = payload if payload is not None else {}
        return eval_context

    def _execute_webhook(self, payload):
        """Execute the webhook for the given payload.
        The payload is a dictionnary that can be used by the `record_getter` to
        identify the record on which the automation should be run.
        """
        self.ensure_one()

        # info logging is done by the ir.http logger
        msg = "Webhook #%s triggered with payload %s"
        msg_args = (self.id, payload)
        _logger.debug(msg, *msg_args)

        record = self.env[self.model_name]
        eval_context = self._get_eval_context(payload=payload)

        if self.record_getter:
            try:
                record = safe_eval(self.record_getter, eval_context)
            except Exception as e:  # noqa: BLE001
                msg = "Webhook #%s could not be triggered because the record_getter failed:\n%s"
                msg_args = (self.id, traceback.format_exc())
                _logger.warning(msg, *msg_args)
                self._webhook_logging(payload, self._add_postmortem(e))
                raise e

        if not record.exists() and self.allow_creation:
            try:
                create_eval_context = self._get_create_eval_context(payload=payload)
                safe_eval(
                    self.create_record_code,
                    create_eval_context,
                    mode="exec",
                    nocopy=True,
                )  # nocopy allows to return 'action'
                record = create_eval_context.get("record", self.model_id.browse())
            except Exception as e:  # noqa: BLE001
                msg = "Webhook #%s failed with error:\n%s"
                msg_args = (self.id, traceback.format_exc())
                _logger.warning(msg, *msg_args)
                self._webhook_logging(payload, self._add_postmortem(e))
        elif not record.exists():
            msg = "Webhook #%s could not be triggered because no record to run it on was found."
            msg_args = (self.id,)
            _logger.warning(msg, *msg_args)
            self._webhook_logging(payload, msg)
            raise exceptions.ValidationError(
                _("No record to run the automation on was found.")
            )

        try:
            # quirk: base.automation(,)._process has a ``context["__action_done"]``
            # at the very beginning of the function while it wasn't set before-hand.
            # so setting this context now to avoid further issue advancing forward.
            if "__action_done" not in self._context:
                self = self.with_context(__action_done={}, payload=payload)
            return self._process(record)
        except Exception as e:  # noqa: BLE001
            msg = "Webhook #%s failed with error:\n%s"
            msg_args = (self.id, traceback.format_exc())
            _logger.warning(msg, *msg_args)
            self._webhook_logging(payload, self._add_postmortem(e))
            raise e
        finally:
            self._webhook_logging(payload, None)

    def _get_create_eval_context(self, payload=None):
        def log(message, level="info"):
            with self.pool.cursor() as cr:
                cr.execute(
                    """
                    INSERT INTO ir_logging(
                        create_date, create_uid, type, dbname, name,
                        level, message, path, line, func
                    )
                    VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.env.uid,
                        "server",
                        self._cr.dbname,
                        __name__,
                        level,
                        message,
                        "action",
                        self.id,
                        self.name,
                    ),
                )

        eval_context = dict(self.env.context)
        model_name = self.model_id.sudo().model
        model = self.env[model_name]
        eval_context.update(
            {
                "uid": self._uid,
                "user": self.env.user,
                "time": tools.safe_eval.time,
                "datetime": tools.safe_eval.datetime,
                "dateutil": tools.safe_eval.dateutil,
                "timezone": timezone,
                "float_compare": float_compare,
                "b64encode": base64.b64encode,
                "b64decode": base64.b64decode,
                "Command": Command,
                "env": self.env,
                "model": model,
                "log": log,
                "payload": payload,
            }
        )
        return eval_context

    def _webhook_logging(self, body, response):
        if self.log_webhook_calls:

            vals = {
                "webhook_type": "incoming",
                "webhook": "%s (%s)" % (self.name, self),
                "endpoint": self.url,
                "headers": "{}",
                "request": ustr(body),
                "body": "{}",
                "response": ustr(response),
                "status": getattr(response, "status_code", None),
            }
            self.env["webhook.logging"].create(vals)

    def _process(self, records, domain_post=None):
        """
        Override to allow delay execution
        """
        to_delay = self.filtered(lambda a: a.delay_execution)
        execute_now = self - to_delay

        super(
            InheritedBaseAutomation,
            to_delay.with_context(delay_execution=True),
        )._process(records, domain_post=domain_post)

        return super(InheritedBaseAutomation, execute_now)._process(
            records, domain_post=domain_post
        )
