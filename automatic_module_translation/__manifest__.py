# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Automatic Translation Tool',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Translate any custom module automatically using PO files.',
    'description': """
        Features
        The Automatic Translation Tool streamlines custom module localization by leveraging machine translation 
        to automatically generate PO files for any language. 
        It intelligently updates the module's i18n directory, saving time and reducing translation costs. """,
    'author': 'Cybrosys Techno Solutions',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/translation_wizard_views.xml',
    ],
    'external_dependencies': {
        'python': ['deep_translator', 'polib'],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',

    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
}
