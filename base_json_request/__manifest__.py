# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Base JSON Request',
    'summary': 'Allows you to receive JSON requests that are not RPC.',
    'version': '10.0.1.0.0',
    'category': 'Authentication',
    'website': 'https://laslabs.com/',
    'author': 'LasLabs, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'installable': True,
    'depends': [
        'web',
    ],
    'post_load': 'post_load',
}
