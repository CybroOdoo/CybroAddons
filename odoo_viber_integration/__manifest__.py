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
    'name': "Viber Integration",
    'version': '20.0.1.0.0',
    'summary': "Open a Viber chat with Odoo users from the systray.",
    'description': 'Adds a systray shortcut that lists the Odoo users and '
                   'opens a Viber chat with the selected user, using the '
                   'phone number saved on their contact.',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'web'],
    'website': "https://www.cybrosys.com",
    'assets': {
        'web.assets_unit_tests': [
            'odoo_viber_integration/static/tests/**/*.test.js',
        ],
        'web.assets_backend': [
            'odoo_viber_integration/static/src/js/viber_integration.js',
            'odoo_viber_integration/static/src/xml/viber_integration_templates.xml',
            'odoo_viber_integration/static/src/scss/viber_integration.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
