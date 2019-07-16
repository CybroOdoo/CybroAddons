# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Avinash Nk(<http://www.cybrosys.com>)
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
    'name': 'Beauty Spa Management',
    'summary': """Beauty Parlour Management with Online Booking System""",
    'version': '9.0.3.0.0',
    'author': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    "category": "Industries",
    'depends': ['base', 'account', 'mail', 'website'],
    'data': ['views/salon_holiday.xml',
             'views/salon_data.xml',
             'views/salon_management_chair.xml',
             'views/salon_management_services.xml',
             'views/salon_order_view.xml',
             'views/salon_management_dashboard.xml',
             'views/booking_backend.xml',
             'views/salon_bookings.xml',
             'views/salon_email_template.xml',
             'views/salon_config.xml',
             'views/working_hours.xml',
             'security/ir.model.access.csv',
             ],
    'demo': [
        'views/booking_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
