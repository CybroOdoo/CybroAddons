# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Import Product variant',
    'version': '20.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': (
        "Import products and product variants via wizard into standard "
        "import view."
    ),
    'description': (
        "This module provides a convenient wizard to import products and "
        "product variants using CSV or Excel files by redirecting to Odoo's "
        "standard import interface."
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'base_import'],
    'data': [
        'security/product_variant_import_groups.xml',
        'security/ir.access.csv',
        'wizards/import_product_variant_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_variant_import/static/src/js/import_action_patch.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
