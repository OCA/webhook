# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from werkzeug.exceptions import BadRequest

from odoo import http


old_handle_exception = http.JsonRequest._handle_exception
old_init = http.JsonRequest.__init__


def __init__(self, *args):
    try:
        old_init(self, *args)
    except BadRequest as e:
        try:
            args = self.httprequest.args
            self.jsonrequest = args
            self.params = json.loads(self.jsonrequest.get('params', "{}"))
            self.context = self.params.pop('context',
                                           dict(self.session.context))
        except ValueError:
            raise e


def _handle_exception(self, exception):
    """ Override the original method to handle Werkzeug exceptions.

    Args:
        exception (Exception): Exception object that is being thrown.

    Returns:
        BaseResponse: JSON Response.
    """

    # For some reason a try/except here still raised...
    code = getattr(exception, 'code', None)
    if code is None:
        return old_handle_exception(
            self, exception,
        )

    error = {
        'data': http.serialize_exception(exception),
        'code': code,
    }

    try:
        error['message'] = exception.description
    except AttributeError:
        try:
            error['message'] = exception.message
        except AttributeError:
            error['message'] = 'Internal Server Error'

    return self._json_response(error=error)
