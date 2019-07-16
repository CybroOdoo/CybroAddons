# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2008-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Car Workshop',
    'version': '9.0.2.0.0',
    'summary': 'Vehicle Workshop Operations & Reports',
    'description': 'Vehicle workshop operations & Its reports',
    'category': 'Industries',
    'author': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'depends': [
                'base',
                'fleet',
                'account_accountant',
                ],
    'data': [
        'views/worksheet_views.xml',
        'views/car_dashboard.xml',
        'views/timesheet_view.xml',
        'views/worksheet_stages.xml',
        'views/vehicle.xml',
        'views/report.xml',
        'views/config_setting.xml',
        'views/workshop_data.xml',
        'security/workshop_security.xml',
        'security/ir.model.access.csv',
    ],

    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
