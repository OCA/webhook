# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import random
import string

from werkzeug.exceptions import Unauthorized

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

try:
    from slugify import slugify
except ImportError:
    _logger.info('`python-slugify` Python library not installed.')


class WebHook(models.Model):

    _name = 'web.hook'
    _description = 'Web Hook'

    name = fields.Char(
        required=True,
    )
    interface = fields.Reference(
        selection='_get_interface_types',
        readonly=True,
        help='This is the interface that the web hook represents. It is '
             'created automatically upon creation of the web hook, and '
             'is also deleted with it.',
    )
    interface_type = fields.Selection(
        selection='_get_interface_types',
        required=True,
    )
    uri = fields.Char(
        help='This is the URI that is used to call the web hook externally.',
        compute='_compute_uri',
    )
    token_id = fields.Many2one(
        string='Token',
        comodel_name='web.hook.token',
    )
    token_type = fields.Selection(
        selection=lambda s: s._get_token_types(),
        required=True,
    )
    token_secret = fields.Char(
        help='This is the secret that is configured for the token exchange. '
             'This configuration is typically performed when setting the '
             'token up in the remote system. For ease, a secure random value '
             'has been provided as a default.',
        default=lambda s: s._default_secret(),
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda s: s.env.user.company_id.id,
    )

    @api.model
    def _get_interface_types(self):
        """Return the web hook interface models that are installed."""
        adapter = self.env['web.hook.adapter']
        return [
            (m, self.env[m]._description) for m in adapter._inherit_children
        ]

    @api.multi
    @api.depends('name')
    def _compute_uri(self):
        for record in self:
            if isinstance(record.id, models.NewId):
                # Do not compute slug until saved
                continue
            name = slugify(record.name or '').strip().strip('-')
            record.uri = '/base_web_hook/%s-%d' % (name, record.id)

    @api.model
    def _get_token_types(self):
        """Return the web hook token interface models that are installed."""
        adapter = self.env['web.hook.token.adapter']
        return [
            (m, self.env[m]._description) for m in adapter._inherit_children
        ]

    @api.model
    def _default_secret(self, length=254):
        characters = string.printable.split()[0]
        return ''.join(
            random.choice(characters) for _ in range(length)
        )

    @api.model
    def create(self, vals):
        """Create the interface for the record and assign to ``interface``."""
        record = super(WebHook, self).create(vals)
        interface = self.env[vals['interface_type']].create({
            'hook_id': record.id,
        })
        record.interface = interface
        return record

    @api.model
    def search_by_slug(self, slug):
        _, record_id = slug.strip().rsplit('-', 1)
        return self.browse(record_id)

    @api.multi
    def receive(self, data=None, data_string=None, headers=None):
        """This method is used to receive a web hook.

        First it extracts the token, then validates using ``token.validate``
        and raises as ``Unauthorized`` if it is invalid. It then passes the
        received data to the underlying interface's ``receive`` method for
        processing, and returns the result. The result returned by the
        interface must be JSON serializable.

        Args:
            data (dict, optional): Parsed data that was received in the
                request.
            data_string (str, optional): The raw data that was received in the
                request body.
            headers (dict, optional): Dictionary of headers that were
                received with the request.

        Returns:
            mixed: A JSON serializable return from the interface's
                ``receive`` method.
        """

        self.ensure_one()

        # Convert optional args to proper types for interfaces
        if data is None:
            data = {}
        if data_string is None:
            data_string = ''
        if headers is None:
            headers = {}

        token = self.interface.extract_token(data, headers)

        if not self.token_id.validate(token, data, data_string, headers):
            raise Unauthorized(_(
                'The request could not be processed: '
                'An invalid token was received.'
            ))

        return self.interface.receive(data, headers)
