# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
{
    'name': 'Event Ticket QR Code Scanner',
    'version': '15.0.1.0.0',
    'category': 'Marketing',
    'summary': 'QR Code Scanner for Event Ticket',
    'description': """This module helps to create QR codes for event tickets,
     scan them, and manage invalid tickets.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_event', 'sale_management'],
    'data': ['views/event_event_ticket.xml',
             'views/event_event_views.xml',
             'views/event_template.xml',
             'report/event_event_templates.xml',
             ],
    'assets': {
        'web.assets_qweb': [
            'event_ticket_qr_scanner/static/src/xml/event_ticket_scan_template.xml',
        ],
        'web.assets_backend': [
            'event_ticket_qr_scanner/static/src/js/event_ticket_scan.js',
            'event_ticket_qr_scanner/static/src/js/html5-qrcode.js',
            'event_ticket_qr_scanner/static/src/css/event_ticket_scan.css',
        ],
    },
    'external_dependencies': {
        'python': ['qrcode']
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
