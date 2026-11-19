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
    'name': 'Warranty Management',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': """Product Warranty, Warranty Claim, Odoo 20 Warranty""",
    'description': """
    Manage product warranties in Odoo 20. Set a warranty duration on
    products, get the warranty expiry date of every sold product on the
    sale order, and let customers submit warranty claims from the website
    and follow their status in the customer portal.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale', 'website'],
    'data': [
        'security/ir.access.csv',
        'data/website_warranty_menu_data.xml',
        'data/portal_entry_data.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/warranty_claim_views.xml',
        'views/website_registration_templates.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'product_warranty_management_odoo/static/src/js/'
            'website_registration.js',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
