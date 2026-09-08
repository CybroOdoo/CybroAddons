# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Waste Management Recycling',
    'version': '19.0.1.0.0',
    'category': 'Operations/Waste Management',
    'summary': 'Material recovery tracking and recycled product sales',
    'description': """
        Tracks the recovery of recyclable materials from waste batches.
        Manages recycling orders, material recovery lines, recovery rates,
        and links recovered materials to Odoo sales orders for revenue tracking.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Technologies Pvt. Ltd.',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'wm_base',
        'wm_collection',
        'sale',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/server_actions.xml',
        'views/recycling_order_views.xml',
        'views/recycling_line_views.xml',
        'views/waste_batch_inherit_views.xml',
        'report/recycling_order_report.xml',
        'views/wm_recycling_efficiency_report_views.xml',
        'views/wm_carbon_accounting_report_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_recycling_orders.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
