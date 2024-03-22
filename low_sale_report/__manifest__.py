# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Low Sales Report",
    'version': '16.0.1.0.0',
    'category': 'Sale',
    'summary': 'The tool to control poorly performing product',
    'description': 'Efficiently manage and analyze low sales with this module,'
                   'offering customizable criteria, flexible reporting '
                   'periods, and versatile presentation options in Odoo or '
                   'Excel. Tailor your analysis by filtering specific product'
                   'categories or sales teams, and choose between '
                   'template-wide insights or focus on individual product '
                   'variants for a comprehensive understanding of '
                   'under performing products.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'crm',],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'report/low_sale_pivot_view_report_view.xml',
        'wizard/low_sale_report_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'low_sale_report/static/src/js/low_sale_xlsx_report.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
