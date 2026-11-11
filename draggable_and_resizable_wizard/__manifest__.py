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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Draggable And Resizable Wizard',
    'version': '20.0.1.0.0',
    'summary': 'Resize every backend wizard and dialog from its corner',
    'description': 'Makes every backend wizard and dialog in Odoo resizable. '
                   'Odoo already lets users move dialogs by their header.',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'draggable_and_resizable_wizard/static/src/dialog/resizable_dialog.js',
            'draggable_and_resizable_wizard/static/src/dialog/resizable_dialog.xml',
            'draggable_and_resizable_wizard/static/src/dialog/resizable_dialog.scss',
        ],
        'web.assets_unit_tests': [
            'draggable_and_resizable_wizard/static/tests/**/*.test.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
