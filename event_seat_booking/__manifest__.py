# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Event Seat Booking',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'The module used to book seats for the event',
    'description': "This module helps  you  to  book seminars, conferences, "
                   "appointments and conventions tickets through website.The "
                   "event managers can add different types of tickets and "
                   "screams in the backend of any event",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'event', 'sale_management', 'website', 'website_event',
                'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/seat_column_sequence.xml',
        'report/event_report_template_full_page_ticket.xml',
        'views/seat_arrangement_views.xml',
        'views/event_event_ticket_views.xml',
        'views/event_event_views.xml',
        'views/event_registration_views.xml',
        'views/seat_arrangement_line_views.xml',
        'views/registration_template.xml',
        'views/event_seat_booking_board_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'event_seat_booking/static/src/js/templates.js',
            'event_seat_booking/static/src/js/register.js',
            'event_seat_booking/static/src/css/template.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
