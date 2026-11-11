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
#############################################################################
{
    'name': 'Fleet Rental Management',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Manage vehicle rentals, recurring contracts, and maintenance checklists.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account', 'fleet', 'mail'],
    'data': [
        'security/fleet_rental_groups.xml',
        'security/ir.access.csv',
        'security/fleet_rental_security.xml',
        'data/fleet_rental_data.xml',
        'data/ir_cron_data.xml',
        'views/car_rental_contract_views.xml',
        'views/car_rental_contract_checklist_views.xml',
        'views/car_tools_views.xml',
        'views/res_config_settings_views.xml',
        'views/fleet_vehicle_views.xml',
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
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
