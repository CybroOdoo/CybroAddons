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
    'name': 'Product Expiry Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Monitor and track product lots and stock batches that are about to expire',
    'description': """The Product Expiry Dashboard provides comprehensive graphical
representations of expired products, near-expiry lots, internal locations, and
warehouses. This module enables users to make critical decisions quickly by
actively monitoring products approaching their expiration dates.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['product_expiry'],
    'data': ['views/product_expiry_dashboard_actions.xml'],
    'assets': {
        'web.assets_backend': [
            'odoo_product_expiry_dashboard/static/src/js/product_expiry_action.js',
            'odoo_product_expiry_dashboard/static/src/xml/odoo_product_expiry_dashboard.xml',
            'odoo_product_expiry_dashboard/static/src/css/style.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
