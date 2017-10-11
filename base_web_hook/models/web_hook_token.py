# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import random
import string

from odoo import api, fields, models


class WebHookToken(models.Model):
    """This represents a generic token for use in a secure web hook exchange.

    It serves as an interface for token adapters. No logic should need to be
    added to this model in inherited modules.
    """

    _name = 'web.hook.token'
    _description = 'Web Hook Token'

    hook_id = fields.Many2one(
        string='Hook',
        comodel_name='web.hook',
        required=True,
        ondelete='cascade',
    )
    token = fields.Reference(
        selection='_get_token_types',
        readonly=True,
        help='This is the token used for hook authentication. It is '
             'created automatically upon creation of the web hook, and '
             'is also deleted with it.',
    )
    token_type = fields.Selection(
        selection='_get_token_types',
        required=True,
    )
    secret = fields.Char(
        help='This is the secret that is configured for the token exchange. '
             'This configuration is typically performed when setting the '
             'token up in the remote system. For ease, a secure random value '
             'has been provided as a default.',
        default=lambda s: s._default_secret(),
    )

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

    @api.multi
    def validate(self, token, data=None, data_string=None, headers=None):
        """This method is used to validate a web hook.

        It simply passes the received data to the underlying token's
        ``validate`` method for processing, and returns the result.

        Args:
            token (mixed): The "secure" token string that should be validated
                against the dataset. Typically a string.
            data (dict, optional): Parsed data that was received with the
                request.
            data_string (str, optional): Raw form data that was received in
                the request. This is useful for computation of hashes, because
                Python dictionaries do not maintain sort order and thus are
                useless for crypto.
            headers (dict, optional): Dictionary of headers that were
                received with the request.

        Returns:
            bool: If the token is valid or not.
        """
        self.ensure_one()
        if data is None:
            data = {}
        if data_string is None:
            data_string = ''
        if headers is None:
            headers = {}
        return self.token.validate(token, data, data_string, headers)
