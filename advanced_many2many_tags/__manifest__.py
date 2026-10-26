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
    'name': 'Advanced Many2Many Tags',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Copy the text and open the form view of many2many tags.',
    'description': """Copy text of Many2many tags, so we can paste it anywhere 
    as needed, and also open the form view of these Many2many fields.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'advanced_many2many_tags/static/src/js/confirmation_dialog_view.js',
            'advanced_many2many_tags/static/src/js/many2many_tags_field.js',
            'advanced_many2many_tags/static/src/xml/many2many_tags_field.xml',
        ],
        'web.assets_unit_tests': [
            'advanced_many2many_tags/static/tests/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
