# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class WebHookRequestBinRequest(models.Model):
    """This is a single request, saved by the RequestBin"""

    _name = 'web.hook.request.bin.request'
    _description = 'Web Hook Request Bin Request'

    bin_id = fields.Many2one(
        string='Request Bin',
        comodel_name='web.hook.request.bin',
        required=True,
        ondelete='cascade',
    )
    uri = fields.Char()
    method = fields.Char()
    headers = fields.Serialized()
    data = fields.Serialized()
    cookies = fields.Serialized()
    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda s: s.env.user.id,
    )
