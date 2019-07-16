# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#
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
    'name': "Cab Booking Management System",
    'summary': """Complete Cab Booking Management and its Related Records""",
    'author': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'category': 'Industries',
    'version': '10.0.1.0.0',
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
