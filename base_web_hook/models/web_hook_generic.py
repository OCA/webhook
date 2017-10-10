# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class WebHookGeneric(models.Model):
    """This is the model that should be inherited for new web hooks."""

    _name = 'web.hook.generic'
    _inherit = 'web.hook.adapter'
    _description = 'Web Hook - Generic'

    @api.multi
    def receive(self, data=None):
        """This should be overridden by inherited models to receive web hooks.

        It can expect a singleton, although can ``self.ensure_one()`` if
        desired.

        Args:
            data (dict, optional): Data that was received with the hook.

        Returns:
            mixed: A JSON serializable return, or ``None``.
        """
        raise NotImplementedError()
