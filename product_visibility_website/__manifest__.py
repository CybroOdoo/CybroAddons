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
    'name': 'Website Product Visibility',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': """Control product and category visibility on the website
    for guests, portal users, and logged-in users.""",
    'description': """This module helps you to make visible only the
    filtered products and product categories for logged-in and
    logged-out users, portal users, and visitors.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml'
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],

    'installable': True,
    'auto_install': False,
    'application': False,
}
