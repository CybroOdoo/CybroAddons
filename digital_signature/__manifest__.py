# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Digital Signature In Purchase Order, Invoice, Inventory',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Enhance Security with Digital Signatures in Purchase Orders, '
               'Invoices, and Inventory',
    'description': """ Secure your business operations with this robust digital 
    signature integration for Odoo. Protect your data and streamline your 
    workflow with Digital Signature In Purchase Order, Invoice, Inventory.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase', 'stock', 'account'],
    'data': [
        'views/account_move_views.xml',
        'views/invoice_report_templates.xml',
        'views/purchase_order_views.xml',
        'views/purchase_report_templates.xml',
        'views/res_config_settings_views.xml',
        'views/stock_picking_report_templates.xml',
        'views/stock_picking_views.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install ': False,
    'application': False,
}
