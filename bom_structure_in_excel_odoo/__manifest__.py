# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "BOM Structure & Cost Report in Excel",
    'version': "16.0.1.0.0",
    'category': 'Manufacturing,Inventory',
    'summary': 'Effortlessly export BOM Structure & Cost Reports to Excel '
               'format',
    'description': 'This app enhances your Odoo experience by enabling the '
                   'export of "BOM Structure & Cost Reports" to Excel format. '
                   'It provides a seamless transition from the standard Odoo '
                   'PDF report to an Excel file, offering flexibility in data '
                   'analysis and presentation.Simply export and analyze your '
                   'BOM reports in Excel with ease.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'mrp'],
    'data': [
        'data/mrp_bom_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bom_structure_in_excel_odoo/static/src/js/action_manager.js',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
