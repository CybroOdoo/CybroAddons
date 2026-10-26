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
    'name': "Ecommerce Sequential Variant Selector",
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': """Sequential attribute selection in odoo eCommerce""",
    'description': "This module enables customers to select product attribute "
                   "values from the website in an ordered manner. It allows "
                   "customers to choose attribute values one by one.",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website_sale'],
    'assets': {
        'web.assets_frontend': [
            'website_sale_variant_selection/static/src/interactions/variant_selection.js',
            'website_sale_variant_selection/static/src/scss/website_sale_attribute_selection.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
