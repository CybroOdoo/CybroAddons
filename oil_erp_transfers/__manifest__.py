# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Oil & Gas Transfers',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Midstream',
    'summary': 'Manage internal transfers using Fleet and Inventory (Stock Picking)',
    'description': """
Internal Transfer module for Oil & Gas ERP.
This module manages movement of materials, fuel, and equipment between locations
using fleet vehicles and stock operations.
Key Features:
- Internal stock transfers between warehouses/sites
- Fleet vehicle assignment for transport
- Driver tracking
- Transfer approval workflow
- Integration with Inventory (stock.picking)
- Integration with Fleet (vehicle usage)
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'stock',
        'fleet',
        'hr',
        'hr_fleet',
        'oil_erp_base',
    ],
    'data': [
        'security/oil_transfer_security.xml',
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
        'views/stock_picking_views.xml',
        'views/oil_transfer_menus.xml',
        'views/stock_picking_reporting_views.xml',
        'wizard/stock_picking_delivery_validation_wizard_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
