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
    'name': 'Digital Signature In Purchase Order, Invoice, Inventory',
    'summary': 'Digital Signature in Purchase Order, Invoice, Inventory',
    'version': '14.0.1.0.0',
    'description': """Digital Signature in Purchase Order, Invoice, Inventory""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase', 'stock', 'account'],
    'data': [
        'views/res_config_settings.xml',
        'views/purchase_order.xml',
        'views/inventory.xml',
        'views/invoice.xml',
        'views/purchase_report_inherit.xml',
        'views/stock_picking_report.xml',
        'views/invoice_report.xml',
    ],
    'installable': True,
    'application': False,
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
}
