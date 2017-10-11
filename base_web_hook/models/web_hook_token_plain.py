# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class WebHookTokenPlain(models.Model):
    """This is a plain text token."""

    _name = 'web.hook.token.plain'
    _inherit = 'web.hook.token.adapter'
    _description = 'Web Hook Token - Plain'

    @api.multi
    def validate(self, token_string, _, _):
        """Return ``True`` if the received token is the same as configured.
        """
        return token_string == self.token_id.secret
