# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Fleet Rental Management',
    'version': '17.0.1.0.0',
    'category': "Services",
    'summary': """This module will helps you to give the vehicles for Rent.""",
    'description': """This module is an application for Vehicle Rental System which helps in managing the rental of vehicles like car,van,bike, jeep etc.
    It manages fleet/vehicle property by extending the basic fleet module of Odoo.
    Currently fleet module does not have any connection with accounting module.
    But in this module, we integrate the module with accounting also.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account', 'fleet', 'mail'],
    'data': [
        'security/fleet_rental_groups.xml',
        'security/fleet_rental_security.xml',
        'security/ir.model.access.csv',
        'data/fleet_rental_data.xml',
        'data/ir_cron_data.xml',
        'views/car_rental_contract_views.xml',
        'views/car_rental_contract_checklist_views.xml',
        'views/car_tools_views.xml',
        'views/res_config_settings_views.xml',
        'reports/report_fleet_rental.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fleet_rental/static/src/xml/timepicker.xml',
            'fleet_rental/static/src/js/time_widget.js',
            'fleet_rental/static/src/scss/timepicker.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
