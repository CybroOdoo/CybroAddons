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
    'name': "Website Helpdesk Management",
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Create helpdesk tickets from the website and manage them with teams, stages, tasks and invoices.',
    'description': """
     Customers create helpdesk tickets from a website form and follow,
     search and download them in their portal. In the backend, the tickets
     move through stages that can email the customer, are shared between
     helpdesk teams, can be merged, turned into project tasks and invoiced
     from the timesheets, and are rated by the customer once closed.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'sale_project', 'hr_timesheet', 'contacts'],
    'data': [
        'security/odoo_website_helpdesk_groups.xml',
        'security/ir.access.csv',
        'data/helpdesk_category_data.xml',
        'data/helpdesk_type_data.xml',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/helpdesk_replay_template_data.xml',
        'data/ticket_stage_data.xml',
        'data/ir_model_data.xml',
        'data/portal_entry_data.xml',
        'views/helpdesk_category_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_type_views.xml',
        'views/merge_ticket_views.xml',
        'views/odoo_website_helpdesk_portal_templates.xml',
        'views/rating_form.xml',
        'report/helpdesk_ticket_report_template.xml',
        'views/res_config_settings_views.xml',
        'views/team_helpdesk_views.xml',
        'views/ticket_helpdesk_views.xml',
        'views/ticket_stage_views.xml',
        'views/website_form.xml',
        'views/helpdesk_menu_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_website_helpdesk/static/src/js/portal_search.js',
        ],
        'web.assets_tests': [
            'odoo_website_helpdesk/static/tests/tours/*.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
