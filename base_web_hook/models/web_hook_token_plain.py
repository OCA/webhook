# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class WebHookTokenUser(models.Model):
    """This is a token that requires a valid user session."""

    _name = 'web.hook.token.user'
    _inherit = 'web.hook.token.adapter'
    _description = 'Web Hook Token - User Session'

    @api.multi
    def validate(self, *_, **__):
        """Return ``True`` if the received token is the same as configured.
        """
        return bool(self.env.user)
