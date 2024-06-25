# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Freight Management',
    'version': '17.0.1.0.1',
    'category': 'Industries',
    'summary': 'Module for Managing All Freight Operations',
    'description': 'From efficient order creation and dynamic shipment planning'
                   'to real-time tracking and meticulous documentation'
                   'management',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'product', 'account'],
    'data': [
        'security/freight_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/freight_routes_data.xml',
        'views/freight_order_views.xml',
        'views/freight_port_views.xml',
        'views/freight_container_views.xml',
        'views/custom_clearance_views.xml',
        'views/freight_service_views.xml',
        'views/order_track_views.xml',
        'report/freight_report_templates.xml',
        'report/tracking_report_templates.xml',
        'wizard/custom_clearance_revision_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
