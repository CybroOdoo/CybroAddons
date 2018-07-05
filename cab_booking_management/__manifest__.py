# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Cab Booking Management System",
    'summary': """Complete Cab Booking Management and its Related Records""",
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Industries',
    'version': '11.0.1.0.0',
    'depends': ['base', 'mail'],
    'data': [
        'views/templates.xml',
        'views/cab_log_view.xml',
        'views/cab_conf_view.xml',
        'views/cab_location_view.xml',
        'views/cab_timing_view.xml',
        'views/cab_booking_view.xml',
        'views/cab_creation_view.xml',
        'views/cab_maintanence_view.xml',
        'security/ir.model.access.csv'
            ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
