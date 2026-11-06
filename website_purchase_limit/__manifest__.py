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
    'name': 'Minimum Purchase Limit In Website',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Helps to set a minimum purchase limit on the website.',
    'description': 'The user can only purchase above the minimum amount configured in the settings',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/website_purchase_limit_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_purchase_limit/static/src/js/website_purchase_limit.js',
            ],
        'web.assets_tests': [
            'website_purchase_limit/static/tests/website_purchase_limit_test.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
