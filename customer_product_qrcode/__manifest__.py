# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Customer and Product QR Code Generator',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Generate Unique QR Codes for Customers and Products',
    'description': '''QR Code, QR Code Generator, Odoo QR Code Generator,
     Customer QR Code, Product QR Code, QR, QR Code Odoo''',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'stock'],
    'data': [
        'data/ir_sequence_data.xml',
        'data/ir_actions_server_data.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'report/customer_product_qrcode_report.xml',
        'report/customer_product_qrcode_template.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
