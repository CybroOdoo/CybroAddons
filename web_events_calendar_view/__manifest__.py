# -*- coding: utf-8 -*-
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
    'name': 'Website Event Calendar View',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Website Calendar View for Events in Odoo 20',
    'description': 'This module helps you create a calendar view of events on '
                   'the website, allowing users to easily navigate to events '
                   'through the calendar.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web', 'website_event'],
    'data': [
        'views/event_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_events_calendar_view/static/src/css/calender.css',
            'web_events_calendar_view/static/src/js/CalendarView.js',
            'web_events_calendar_view/static/src/xml/templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
