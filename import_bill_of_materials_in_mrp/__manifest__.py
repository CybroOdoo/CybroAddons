# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (<https://www.cybrosys.com>)
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
    'name': 'Import Bill Of Materials',
    'version': '15.0.1.0.0',
    'category': 'Manufacturing',
    'summary': """Import Bill of materials using CSV, Excel file""",
    'description': 'Using this module we can import bom by searching'
                   ' the products in different ways in csv or excel files',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'stock', 'mrp'],
    'data': {
        'security/import_bom_security.xml',
        'security/ir.model.access.csv',
        'views/bom_import_menu_views.xml',
        'wizards/bom_import_views.xml',
        'wizards/success_message_views.xml',
    },
    'assets': {
        'web.assets_backend': [
            'import_bill_of_materials_in_mrp/static/src/css/style.css'
        ],
    },
    'external_dependencies': {
        'python': [
            'openpyxl'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
