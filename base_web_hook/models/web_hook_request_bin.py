# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import pprint

from odoo import api, fields, models
from odoo.http import request


class WebHookRequestBin(models.Model):
    """This is an abstract Request Bin to be used for testing web hooks.

    It simply saves the request data for later evaluation. This is incredibly
    useful when implementing web hook from undocumented sources.
    """

    _name = 'web.hook.request.bin'
    _description = 'Web Hook - Request Bin'
    _inherit = 'web.hook.adapter'

    request_ids = fields.One2many(
        string='Requests',
        comodel_name='web.hook.request.bin.request',
        inverse_name='bin_id',
    )

    @api.multi
    def receive(self, data, headers):
        """Capture the request.

        Args:
            data (dict): Data that was received with the hook.
            headers (dict): Headers that were received with the request.
        """
        self.env['web.hook.request.bin.request'].create({
            'bin_id': self.id,
            'uri': request.httprequest.url,
            'method': request.httprequest.method,
            'headers': pprint.pformat(dict(headers), indent=4),
            'data_parsed': pprint.pformat(data, indent=4),
            'data_raw': request.httprequest.get_data(),
            'cookies': pprint.pformat(request.httprequest.cookies,
                                      indent=4),
        })

    @api.multi
    def extract_token(self, data, headers):
        """No tokens are required in this implementation."""
        return True
