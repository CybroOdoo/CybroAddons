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
    'name': 'Autosuggestion in Discuss',
    'version': '20.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Show auto suggestion in chat in Odoo.',
    'description': 'Previous messages of user will be '
                   'shown as autosuggestion in the chat.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'assets': {
        'web.assets_backend': [
            'autosuggestion_in_discuss/static/src/scss/autosuggest.scss',
            'autosuggestion_in_discuss/static/src/xml/composer_view.xml',
            'autosuggestion_in_discuss/static/src/js/composer.js',
        ],
        'web.assets_unit_tests': [
            'autosuggestion_in_discuss/static/tests/composer.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
