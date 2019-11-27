# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Base Web Hook',
    'summary': 'Provides an abstract system for defining and receiving web '
               'hooks.',
    'version': '10.0.1.0.0',
    'category': 'Tools',
    'website': 'https://laslabs.com/',
    'author': 'LasLabs, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'installable': True,
    'external_dependencies': {
        'python': ['slugify'],
    },
    'depends': [
        'base_json_request',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/web_hook_view.xml',
    ],
}
