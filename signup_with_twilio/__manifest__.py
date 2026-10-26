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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'SignUp With Mobile',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Sign up with mobile number verified via Twilio SMS OTP.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['portal', 'auth_signup', 'mail'],
    'data': [
        'views/res_config_setting_views.xml',
        'views/signup_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'signup_with_twilio/static/src/css/signup.css',
            'signup_with_twilio/static/src/js/signup.js',
        ],
    },
    'external_dependencies': {
        'python': ['twilio'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
