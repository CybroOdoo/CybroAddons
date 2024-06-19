# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Website Helpdesk Support Ticket Management",
    'version': '16.0.3.0.0',
    'category': 'Website',
    'summary': """Helpdesk Module for community""",
    'description': 'Can create ticket from website also and can manage it from'
                   ' backend.Bill can be created for ticket with service cost',
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'website', 'project', 'sale_project',
                'hr_timesheet', 'mail', 'contacts'],
    'data': [
        'security/odoo_website_helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ticket_stage_data.xml',
        'data/helpdesk_types_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/help_team_views.xml',
        'views/portal_search_templates.xml',
        'views/res_config_settings_views.xml',
        'views/website_form.xml',
        'views/report_templates.xml',
        'views/help_ticket_views.xml',
        'views/portal_views_templates.xml',
        'views/helpdesk_categories_views.xml',
        'views/rating_form_templates.xml',
        'views/merge_tickets_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_types_views.xml',
        'views/ticket_stage_views.xml',
        'views/helpdesk_replay_template.xml',
        'views/odoo_website_helpdesk_menus.xml',
        'report/help_ticket_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_website_helpdesk/static/src/xml/help_ticket_templates.xml',
            'odoo_website_helpdesk/static/src/js/helpdesk_dashboard_action.js',
        ],
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/ticket_details.js',
            '/odoo_website_helpdesk/static/src/js/portal_groupby_and_search.js',
            '/odoo_website_helpdesk/static/src/js/multiple_product_choose.js',
            '/odoo_website_helpdesk/static/src/cdn/jquery.sumoselect.min.js',
            '/odoo_website_helpdesk/static/src/cdn/sumoselect.min.css',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
