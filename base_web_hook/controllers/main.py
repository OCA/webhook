# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http


class WebHookController(http.Controller):

    @http.route(
        ['/base_web_hook/<string:slug>'],
        type='json',
        auth='none',
    )
    def receive(self, slug, **kwargs):
        hook = self.env['web.hook'].search_by_slug(slug)
        return hook.receive(
            data=kwargs,
            data_string=http.request.httprequest.get_data(),
            headers=http.request.httprequest.headers,
        )
