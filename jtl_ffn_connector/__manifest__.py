# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'JTL FFN Connector',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Logistics',
    'summary': 'Full integration with JTL Fulfillment Network (FFN): products, stock, orders, tracking, returns, multi-warehouse',
    'description':'Synchronizing warehouses,products, stock, orders and returns between odoo and jtl for merchants ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': [
        'stock',
        'sale_management',
        'delivery',
        'mail',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/jtl_ffn_sequence.xml',
        'data/jtl_ffn_cron.xml',
        'views/jtl_ffn_config_views.xml',
        'views/jtl_ffn_warehouse_views.xml',
        'views/jtl_ffn_product_views.xml',
        'views/jtl_ffn_order_views.xml',
        'views/jtl_ffn_return_views.xml',
        'views/jtl_ffn_menu.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
}
