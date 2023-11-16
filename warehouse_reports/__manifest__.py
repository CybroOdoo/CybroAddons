# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Warehouse Reports",
    "version": "16.0.1.0.0",
    "category": "Warehouse",
    "summary": "All warehouse related PDF and Excel reports",
    "description": "User is able to print Pdf and Excel report of Stock move,"
                   "Transfer,Product,Stock valuation.All warehouse related PDF"
                   "and Excel report",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_valuation_report_views.xml',
        'wizards/stock_move_report_views.xml',
        'report/ir_action_reports.xml',
        'report/stock_valuation_report_templates.xml',
        'report/stock_transfer_report_templates.xml',
        'report/stock_move_report_templates.xml',
        'report/stock_product_report_templates.xml',
        'wizards/stock_product_report_views.xml',
        'wizards/stock_transfer_report_views.xml',
        'views/warehouse_reports_menus.xml'
    ],
    'assets':
        {
            'web.assets_backend': [
                'warehouse_reports/static/src/js/stock_excel_report.js'
            ],
        },
    'images': [
        'static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
