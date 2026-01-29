# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Odoo Professional Report Templates',
    'version': '15.0.1.0.0',
    'category': 'Sales,Purchases,Accounting,Warehouse',
    'summary': "Change design of report of sale order, purchase order, "
               "invoice and stock",
    'description': "To tailor the presentation of different reports such as "
                   "Sales Orders, Purchase Orders, Invoices, and Delivery "
                   "Orders, the process involves customizing the report "
                   "templates , especially for PDF reports By doing so, "
                   "you can personalize the design,content of these reports to"
                   "better suit your business needs and preferences.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'account', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/doc_layout_data.xml',
        'report/purchase_order_reports.xml',
        'report/purchase_order_traditional_templates.xml',
        'report/purchase_order_standard_templates.xml',
        'report/purchase_order_modern_templates.xml',
        'report/purchase_order_attractive_templates.xml',
        'report/sale_order_reports.xml',
        'report/sale_order_traditional_templates.xml',
        'report/sale_order_standard_templates.xml',
        'report/sale_order_modern_templates.xml',
        'report/sale_order_attractive_templates.xml',
        'report/stock_move_reports.xml',
        'report/stock_move_traditional_templates.xml',
        'report/stock_move_standard_templates.xml',
        'report/stock_move_modern_templates.xml',
        'report/stock_move_attractive_templates.xml',
        'report/account_move_reports.xml',
        'report/account_move_traditional_templates.xml',
        'report/account_move_standard_templates.xml',
        'report/account_move_modern_templates.xml',
        'report/account_move_attractive_templates.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_move_views.xml',
        'views/doc_layout_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

