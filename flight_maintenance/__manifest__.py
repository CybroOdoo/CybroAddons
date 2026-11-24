# -*- coding: utf-8 -*-
#############################################################################
#
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
    'name': 'Flight Maintenance',
    'version': '19.0.1.0.0',
    'category': 'Operations/Flight Operations',
    'summary': 'Aircraft airworthiness gating (via Odoo Maintenance) and running aircraft metrics',
    'description': """
Flight Maintenance
====================
Keeps unfit aircraft out of the schedule and tracks the metrics that drive
maintenance timing. Built on top of Odoo's native Maintenance app rather
than a custom work-order model, so aircraft maintenance shows up alongside
any other equipment maintenance the organization already tracks.

Features
--------
* Each aircraft is auto-linked to a maintenance.equipment record
* Maintenance requests (maintenance.request) can be marked as grounding an
  aircraft; while such a request is open, the aircraft is automatically
  blocked from being scheduled or dispatched
* Running aircraft metrics (airframe hours, engine hours, cycles, fuel used)
  that accumulate automatically as flights are completed
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['flight_management', 'maintenance'],
    'data': [
        'security/flight_maintenance_groups.xml',
        'security/ir.model.access.csv',
        'data/flight_maintenance_equipment_category_data.xml',
        'views/flight_maintenance_request_views.xml',
        'views/flight_aircraft_metric_views.xml',
        'views/flight_aircraft_views.xml',
        'views/flight_maintenance_menus.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
