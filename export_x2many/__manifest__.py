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
    'name': 'Export X2Many',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Export x2many child fields and generate multi-sheet Excel workbooks',
    'description': """
    Export X2Many
    =============
    Added features of selecting direct subfields and option to split workbook
    to sheets based on field value in export functionality. Allows to export
    data as filtered data in multiple fields.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'export_x2many/static/src/xml/export_data_dialog.xml',
            'export_x2many/static/src/xml/groupby_sheet_dialog.xml',
            'export_x2many/static/src/js/export_data_dialog.js',
            'export_x2many/static/src/js/groupby_sheet_dialog.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
