# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class WebHookTokenNone(models.Model):
    """This is a token that will validate under all circumstances."""

    _name = 'web.hook.token.none'
    _inherit = 'web.hook.token.adapter'
    _description = 'Web Hook Token - None'

    @api.multi
    def validate(self, token_string, *_, **__):
        """Return ``True`` if the received token is the same as configured.
        """
        return True
