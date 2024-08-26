# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import uuid

from odoo import fields, models


class WebhookLog(models.Model):
    _name = "webhook.logging"
    _description = "Webhook Logging"
    _order = "id DESC"

    name = fields.Char(string="Reference", default=lambda self: str(uuid.uuid4()))
    webhook_type = fields.Selection(
        selection=[
            ("incoming", "Incoming"),
            ("outgoing", "Outgoing"),
        ],
        string="Type",
    )
    webhook = fields.Char()
    endpoint = fields.Char()
    headers = fields.Char()
    status = fields.Char()
    body = fields.Text()
    request = fields.Text()
    response = fields.Text()
