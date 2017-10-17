# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo import http


class WebHookController(http.Controller):

    @http.route(
        ['/base_web_hook/json/<string:slug>.json'],
        type='json',
        auth='public',
    )
    def json_receive(self, *args, **kwargs):
        return self._receive(*args, **kwargs)

    @http.route(
        ['/base_web_hook/<string:slug>'],
        type='http',
        auth='public',
    )
    def http_receive(self, *args, **kwargs):
        return json.dumps(
            self._receive(*args, **kwargs),
        )

    def _receive(self, slug, **kwargs):
        hook = http.request.env['web.hook'].search_by_slug(slug)
        return hook.receive(
            data=kwargs,
            data_string=http.request.httprequest.get_data(),
            headers=http.request.httprequest.headers,
        )
