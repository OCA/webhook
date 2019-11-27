# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class WebHookAdapter(models.AbstractModel):
    """This is the model that should be inherited for new web hooks."""

    _name = 'web.hook.adapter'
    _description = 'Web Hook Adapter'
    _inherits = {'web.hook': 'hook_id'}

    hook_id = fields.Many2one(
        string='Hook',
        comodel_name='web.hook',
        required=True,
        ondelete='cascade',
    )

    @api.model
    def create(self, vals):
        """If creating from the adapter level, circumvent adapter creation.

        An adapter is implicitly created and managed from within the
        ``web.hook`` model. This is desirable in most instances, but it should
        also be possible to create an adapter directly.
        """
        context_self = self.with_context(web_hook_no_interface=True)
        return super(WebHookAdapter, context_self).create(vals)

    @api.multi
    def receive(self, data, headers):
        """This should be overridden by inherited models to receive web hooks.

        The data has already been authenticated at this point in the workflow.

        It can expect a singleton, although can ``self.ensure_one()`` if
        desired.

        Args:
            data (dict): Data that was received with the hook.
            headers (dict): Headers that were received with the request.

        Returns:
            mixed: A JSON serializable return, or ``None``.
        """
        raise NotImplementedError()

    @api.multi
    def extract_token(self, data, headers):
        """Extract the token from the data and return it.

        Args:
            data (dict): Data that was received with the hook.
            headers (dict): Headers that were received with the request.

        Returns:
            mixed: The token data. Should be compatible with the hook's token
                interface (the ``token`` parameter of ``token_id.validate``).
        """
        raise NotImplementedError()
