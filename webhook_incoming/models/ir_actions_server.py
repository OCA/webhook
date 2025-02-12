# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def run(self):
        if self.env.context.get("delay_execution"):
            return self.with_delay().run()
        return super().run()

    @api.model
    def _job_prepare_context_before_enqueue_keys(self):
        return (
            "active_model",
            "active_ids",
            "active_id",
            "domain_post",
        )
