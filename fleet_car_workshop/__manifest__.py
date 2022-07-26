# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWATHI C (<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Car Workshop',
    'version': '14.0.1.0.0',
    'summary': 'Complete Vehicle Workshop Operations & Reports',
    'description': 'Vehicle workshop operations & Its reports',
    'category': 'Industries',
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'depends': [
        'base',
        'fleet',
        'stock',
        'account',
    ],
    'data': [
        'data/workshop_data.xml',
        'views/worksheet_views.xml',
        'views/configuration_settings_view.xml',
        'views/car_dashboard.xml',
        'views/timesheet_view.xml',
        'views/worksheet_stages.xml',
        'views/vehicle.xml',
        'views/report.xml',
        'security/workshop_security.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
