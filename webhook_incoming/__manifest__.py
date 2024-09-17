# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Incoming Webhook",
    "summary": "Receive incoming webhook requests as trigger to execute tasks.",
    "version": "17.0.0.0.1",
    "author": "Hoang Tran,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/webhook",
    "depends": ["base_automation", "webhook_outgoing", "queue_job"],
    "data": [
        "views/base_automation_views.xml",
    ],
    "auto_install": True,
}
