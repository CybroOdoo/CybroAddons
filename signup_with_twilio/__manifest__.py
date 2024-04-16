# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'SignUp With Mobile',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'A Module For SignUp With Mobile Number.',
    'description': """Module helps users sign up using their mobile number
    and verify it with a one-time password (OTP) by Twilio. Additionally, the
     option to sign up with an email ID is also available""",
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
            'signup_with_twilio/static/**/*',
        ],
    },
    'external_dependencies': {
        'python': ['twilio']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
