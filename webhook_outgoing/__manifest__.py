# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Outgoing Webhook",
    "summary": "Webhook to publish events based on automated triggers",
    "version": "16.0.0.0.1",
    "author": "Hoang Tran,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/webhook",
    "depends": [
        "base_automation",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/queue_data.xml",
        "views/webhook_logging_views.xml",
        "views/ir_action_server_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
