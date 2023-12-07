# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': '16.0.4.0.1',
    'summary': """Helpdesk Module for community""",
    'description': """Can create ticket from website also and can manage it from backend.
    Bill can be created for ticket with service cost""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Website',
    'depends': ['base', 'website', 'project', 'sale_project', 'hr_timesheet',
                'mail', 'contacts'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/ticket_sequence.xml',
        'data/ticket_stage_data.xml',
        'data/ticket_type.xml',
        'data/ticket_auto_close.xml',
        'data/rating_template.xml',
        'views/team.xml',
        'views/portal_search.xml',
        'views/res_config_settings.xml',
        'views/website_form.xml',
        'views/report.xml',
        'views/helpdesk.xml',
        'views/helpdesk_views.xml',
        'views/portal.xml',
        'views/categories.xml',
        'views/rating_form.xml',
        'views/merge_tickets_views.xml',
        'templates/helpdesk_replay_template.xml',
        'report/helpdesk_ticket_report_template.xml',
    ],
    'assets': {
        # 'web.assets_frontend': [
        # ],
        'web.assets_backend': [
            'odoo_website_helpdesk/static/src/xml/helpdesk_dashboard.xml',
            'odoo_website_helpdesk/static/src/js/helpdesk_dashboard_action.js',
        ],
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/ticket_details.js',
            '/odoo_website_helpdesk/static/src/js/portal_search.js',
            '/odoo_website_helpdesk/static/src/js/portal_groupby.js',
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
