# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nihala KP(<https://www.cybrosys.com>)
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
    'name': 'Parking Management',
    'version': '15.0.1.0.0',
    'category': 'Industries',
    'summary': 'Manage the parking of vehicles',
    'description': 'This module is developed for managing the vehicle parking'
                   'and providing the tickets for any type of customers',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base','fleet','account'],
    'data':[
        'security/odoo_parking_management_groups.xml',
        'security/parking_entry_security.xml',
        'security/ir.model.access.csv',
        'data/report_paperformat_data.xml',
        'data/ir_sequence_data.xml',
        'report/parking_ticket_report_templates.xml',
        'wizard/register_payment_views.xml',
        'views/parking_entry_views.xml',
        'views/slot_type_views.xml',
        'views/location_details_views.xml',
        'views/slot_details_views.xml',
        'views/member_slot_reservation_views.xml',
        'views/vehicle_details_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
