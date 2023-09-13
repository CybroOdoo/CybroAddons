# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Website HelpDesk Dashboard",
    'version': '15.0.1.0.0',
    'category': 'Website',
    'summary': 'Website HelpDesk Dashboard Module Brings a Multipurpose '
               'Graphical Dashboard for Website HelpDesk module',
    'description': 'Helps to show a dashboard view of helpdesk module.We will '
                   'get the details of helpdesk teams, received tickets, '
                   'tickets based on month, ticket count ratio by teams, '
                   'tickets by project ratio, Billed tasks by team ratio, '
                   'Resolved tickets and  New, In-progress and Closed tickets.',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['odoo_website_helpdesk', 'base'],
    'data': [
        'views/help_ticket_views.xml',
        'views/dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_website_helpdesk_dashboard/static/src/css/dashboard.css',
            'odoo_website_helpdesk_dashboard/static/src/js/lib/Chart.bundle.js',
            'odoo_website_helpdesk_dashboard/static/src/js/dashboard_view.js'
        ],
        'web.assets_qweb': [
            'odoo_website_helpdesk_dashboard/static/src/xml/helpdesk_dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
