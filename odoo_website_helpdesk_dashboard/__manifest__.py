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
    'name': 'Website HelpDesk Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'See the tickets, priorities and teams of the Website '
               'HelpDesk on one graphical dashboard.',
    'description': """
        Adds a dashboard to the Website HelpDesk app with the number of new,
        in progress and done tickets, the helpdesk teams, the priority of the
        tickets, the customer reviews, a chart of the ticket status, a chart
        of the tickets per team and the latest tickets.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['odoo_website_helpdesk'],
    'data': [
        'views/menu_item.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_website_helpdesk_dashboard/static/src/js/dashboard_view.js',
            'odoo_website_helpdesk_dashboard/static/src/xml/dashboard_view.xml',
            'odoo_website_helpdesk_dashboard/static/src/scss/dashboard.scss',
        ],
        'web.assets_tests': [
            'odoo_website_helpdesk_dashboard/static/tests/tours/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
