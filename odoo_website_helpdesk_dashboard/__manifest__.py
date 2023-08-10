# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
    'name': "Website Helpdesk Dashboard",
    'version': '14.0.1.0.0',
    'category': 'Website',
    'summary': 'Website HelpDesk Dashboard module Brings a multipurpose '
               'graphical dashboard for Website Helpdesk Support Ticket '
               'Management module',
    'description': 'Helps to show a dashboard view of Website Helpdesk Support '
                   'Ticket Management module.We will get the details of '
                   'helpdesk teams, received tickets, tickets based on month, '
                   'ticket count ratio by teams, tickets by project ratio, '
                   'Billed tasks by team ratio, Resolved tickets and  New, '
                   'In-progress and Closed tickets.',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['odoo_website_helpdesk', 'base'],
    'data': [
        'views/help_ticket_views.xml',
        'views/assets.xml',
        'views/dashboard_templates.xml'
    ],
    'qweb': [
        "static/src/xml/helpdesk_dashboard_templates.xml"
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
