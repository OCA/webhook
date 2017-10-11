# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class WebHookTokenAdapter(models.AbstractModel):
    """This should be inherited by all token interfaces."""

    _name = 'web.hook.token.adapter'
    _description = 'Web Hook Token Adapter'

    token_id = fields.Many2one(
        string='Token',
        comodel_name='web.hook.token',
        required=True,
        ondelete='cascade',
    )

    @api.multi
    def validate(self, token_string, data, data_string, headers):
        """Return ``True`` if the token is valid. Otherwise, ``False``.

        Child models should inherit this method to provide token validation
        logic.

        Args:
            token_string (str): The "secure" token string that should be
                validated against the dataset.
            data (dict): Parsed data that was received with the request.
            data_string (str): Raw form data that was received in
                the request. This is useful for computation of hashes, because
                Python dictionaries do not maintain sort order and thus are
                useless for crypto.
            headers (dict): Dictionary of headers that were received with the
                request.

        Returns:
            bool: If the token is valid or not.
        """
        raise NotImplementedError()
