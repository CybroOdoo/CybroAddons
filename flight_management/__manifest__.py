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
    'name': 'Flight Management',
    'version': '19.0.1.0.0',
    'category': 'Operations/Flight Operations',
    'summary': 'Base module for managing flights, aircraft, and aerodromes',
    'description': """
Flight Management
==================
Foundational module holding the core flight, aircraft, and aerodrome data
that other Flight Operations modules (scheduling, maintenance, commercial)
build on top of.

Features
--------
* Flight records with a basic lifecycle (draft -> scheduled -> dispatched
  -> in_progress -> completed / cancelled)
* Aircraft register, classified by make / model / class
* Aerodrome (airport) reference data
* Flight events (takeoff, landing, and other timestamped phase markers)
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/flight_management_groups.xml',
        'security/ir.model.access.csv',
        'data/flight_sequence_data.xml',
        'views/flight_aircraft_views.xml',
        'views/flight_aerodrome_views.xml',
        'views/flight_flight_views.xml',
        'views/flight_event_views.xml',
        'views/flight_management_menus.xml',
    ],
    'demo': [
        'demo/flight_management_demo.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
