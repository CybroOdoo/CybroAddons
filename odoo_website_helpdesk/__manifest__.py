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
    'name': "Website Helpdesk Support Ticket Management",
    'version': '14.0.1.0.0',
    'category': 'Website',
    'summary': 'Create helpdesk tickets from website. It is often used to '
               'track customer requests and provide customer support promptly '
               'and efficiently',
    'description': 'From the website, create helpdesk tickets. It is '
                   'frequently used to keep track of customer requests and '
                   'deliver timely, effective customer service.',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'depends': ['sale_project', 'hr_timesheet', 'website_form'],
    'data': [
        'security/ir.model.access.csv',
        'data/ticket_sequence_data.xml',
        'data/ticket_stage_data.xml',
        'report/report_ticket_templates.xml',
        'views/help_ticket_views.xml',
        'views/help_team_views.xml',
        'views/ticket_stage_views.xml',
        'views/res_config_settings_views.xml',
        'views/odoo_website_helpdesk_menus.xml',
        'views/website_form_templates.xml',
        'views/portal_templates.xml',
        'views/asset_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
