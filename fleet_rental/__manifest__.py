# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AGPL (v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AGPL (AGPL v3) for more details.
#
##############################################################################

{
    'name': 'Fleet Rental Management',
    'version': '12.0.1.0.0',
    'summary': """This module will helps you to give the vehicles for Rent.""",
    'description': "Module Helps You To Manage Rental Contracts",
    'category': "Industries",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'account', 'fleet', 'mail'],
    'data': ['security/rental_security.xml',
             'security/ir.model.access.csv',
             'views/car_rental_view.xml',
             'views/checklist_view.xml',
             'views/car_tools_view.xml',
             'reports/rental_report.xml',
             'data/fleet_rental_data.xml',
             ],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
