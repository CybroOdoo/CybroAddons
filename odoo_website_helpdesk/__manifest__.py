# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
{
    'name': "Website Helpdesk Support Ticket Management",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Website Helpdesk Support Ticket Management for Odoo 15 '
               'Community',
    'description': 'This module adds support ticket management functionality '
                   'to your website helpdesk, allowing your customers to '
                   'easily create, view, and respond to support tickets.',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'depends': ['website', 'sale_project', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'data/ticket_sequence_data.xml',
        'data/ticket_stage_data.xml',
        'report/help_ticket_reports.xml',
        'report/help_ticket_templates.xml',
        'views/ticket_stage_views.xml',
        'views/help_ticket_views.xml',
        'views/help_team_views.xml',
        'views/portal_templates.xml',
        'views/res_config_settings_views.xml',
        'views/website_form_views.xml',
        'views/odoo_website_helpdesk_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/ticket_details.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
