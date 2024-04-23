# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Odoo Professional Report Templates',
    'version': '17.0.1.0.0',
    'category': 'Sales,Purchases,Accounting,Warehouse',
    'summary': "Report Templates, Professional Report Templates, Report Customisations, Sale Reports, Purchase Reports, Invoice Reports, Templates, Odoo17, Oodoo Apps",
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
    'depends': ['base', 'sale_management', 'account', 'stock', 'purchase'],
    'data': [
        'data/doc_layout_data.xml',
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/doc_layout_views.xml',
        'views/purchase_traditional_templates.xml',
        'views/purchase_standard_templates.xml',
        'views/purchase_modern_templates.xml',
        'views/purchase_attractive_templates.xml',
        'views/sale_traditional_templates.xml',
        'views/sale_standrd_templates.xml',
        'views/sale_modern_templates.xml',
        'views/sale_attractive_templates.xml',
        'views/stock_traditional_templates.xml',
        'views/stock_standard_templates.xml',
        'views/stock_modern_templates.xml',
        'views/stock_attractive_templates.xml',
        'views/account_traditional_templates.xml',
        'views/account_standrd_templates.xml',
        'views/account_modern_templates.xml',
        'views/account_attractive_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
