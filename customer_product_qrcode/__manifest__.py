# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Ayana KP(<https://www.cybrosys.com>)

#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Customer and Product QR Code Generator',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Generate Unique QR Codes for Customers and Products',
    'description': '''QR Code, QR Code Generator, Odoo QR Code Generator,
    Customer QR Code, Product QR Code, QR, QR Code Odoo''',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'stock'],
    'data': [
        'data/sequence.xml',
        'data/ir_actions_server_data.xml',
        'views/res_config_settings_view.xml',
        'views/res_partner_view.xml',
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'report/paperformat.xml',
        'report/report_action.xml',
        'report/customer_product_qrcode_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

