# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Technical',
    'summary': 'Odoo Professional Report Templates',
    'description': """Report Maker, Report Creator, Odoo Professional Report Templates, Report Templates, Templates, Customizable Report Template for Sale, Invoice, Delivery Order,Purchases""",
    'depends': ['base', 'sale_management', 'account', 'stock', 'purchase'],
    'data': [
        'data/design_templates.xml',
        'security/ir.model.access.csv',
        'views/company_report_template.xml',
        'views/sale_ordeline_image.xml',
        'views/purchase_orderline_image.xml',
        'views/account_line_image.xml',
        'views/stock_move_image.xml',
        'views/custom_layouts.xml',
        'purchase_custom_reports/purchase_traditional_template.xml',
        'purchase_custom_reports/purchase_standard_template.xml',
        'purchase_custom_reports/purchase_modern_template.xml',
        'purchase_custom_reports/purchase_attractive_template.xml',
        'sale_custom_reports/sale_traditional_template.xml',
        'sale_custom_reports/sale_standrd_template.xml',
        'sale_custom_reports/sale_modern_template.xml',
        'sale_custom_reports/sale_attractive_template.xml',
        'stock_custom_template/delivery_traditional.xml',
        'stock_custom_template/delivery_standard.xml',
        'stock_custom_template/delivery_modern.xml',
        'stock_custom_template/delivery_slip_attractive.xml',
        'account_custom_templates/account_traditional.xml',
        'account_custom_templates/account_standrd_template.xml',
        'account_custom_templates/account_modern_template.xml',
        'account_custom_templates/account_attractive_template.xml',

    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
