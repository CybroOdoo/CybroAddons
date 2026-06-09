# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Advance Product Dimension',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Manage product dimensions like width, height, and length.""",
    'description': """This module allows you to add and manage product dimensions in Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'purchase', 'account', 'stock', 'mrp'],
    'data': [
        'views/product_product_views.xml',
        'views/sale_order_views.xml',
        'views/sale_pdf_report_template.xml',
        'views/purchase_order_views.xml',
        'views/purchase_pdf_report_template.xml',
        'views/purchase_order_templates_views.xml',
        'views/report_invoice.xml',
        'views/mrp_production_templates.xml',
        'views/account_move_views.xml',
        'views/mrp_production_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
