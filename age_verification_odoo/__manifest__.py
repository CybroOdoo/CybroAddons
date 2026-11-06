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
    'name': 'Age Verification in Website Login',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Ask for a date of birth before visitors can sign up on the '
               'website.',
    'description': 'Keeps the website signup form locked behind an age '
                   'verification popup. Visitors under 18 see an access '
                   'denied message and cannot fill in the form.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'auth_signup'],
    'data': [
        'views/website_layout_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'age_verification_odoo/static/src/css/age_form.css',
            'age_verification_odoo/static/src/js/age_verification.js',
        ],
        'web.assets_tests': [
            'age_verification_odoo/static/tests/tours/age_verification_tour.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
