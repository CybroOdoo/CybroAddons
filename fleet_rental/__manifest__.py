# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technogies @cybrosys(odoo@cybrosys.com)
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
#############################################################################

{
    'name': 'Fleet Rental Management',
    'version': '16.0.1.0.0',
    'summary': """This module will helps you to give the vehicles for Rent.""",
    'description': "Module Helps You To Manage Rental Contracts, Odoo16, Odoo 16, Fleet, Rental, Rent, Vehicle management",
    'category': "Services",
    'live_test_url': 'https://youtu.be/chN-n7nB3Ac',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'account', 'fleet', 'mail'],
    'data': [
        'data/fleet_rental_data.xml',
        'security/rental_security.xml',
        'security/ir.model.access.csv',
        'views/car_rental_view.xml',
        'views/checklist_view.xml',
        'views/car_tools_view.xml',
        'views/res_config_settings_views.xml',
        'reports/rental_report.xml'
    ],
    "assets": {
        'web.assets_backend': [
            'fleet_rental/static/src/js/time_widget.js',
            'fleet_rental/static/src/xml/timepicker.xml',
            'fleet_rental/static/src/scss/timepicker.scss'
        ],
    },
    'demo': [
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
