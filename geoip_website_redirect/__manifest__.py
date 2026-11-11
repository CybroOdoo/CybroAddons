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
    'name': 'Website Geolocation Based Language and Currency',
    'version': '20.0.1.0.0',
    'category': 'eCommerce, Productivity',
    'summary': 'Website Geolocation Based Language and Currency for Odoo 20',
    'description': """The module helps you to map currency and language
    based on User's IP address""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': ['views/login_template.xml'],
    'assets': {
        'web.assets_frontend': [
            'geoip_website_redirect/static/src/js/userIpAddress.js',
        ],
    },
    'external_dependencies': {
        'python': ['countryinfo'],
    },
    'images': ['static/description/banner.jpg'],
    'post_init_hook': '_post_init_hook',
    'license': 'LGPL-3',
    'installable': True,
   
    'auto_install': False,
    'application': False,
}
