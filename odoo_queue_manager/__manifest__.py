# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Queue Manager',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Manage customer queue, token generation, and counter operations',
    'description': 'A simple queue management system with token generation, department-wise queues, and counter processing.',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'contacts', 'website_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/website_menu_data.xml',
        'views/token_interface_views.xml',
        'views/generate_token_template.xml',
        'views/department_views.xml',
        'views/token_session_views.xml',
        'views/token_token_views.xml',
        'views/queue_counter_views.xml',
        'views/queue_process_views.xml',
        'views/queue_display_views.xml',
        'views/dashboard_actions.xml',
        'views/menus.xml',
        'report/employee_idea_report_templates.xml',
        'wizard/select_department_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_queue_manager/static/src/css/styles.css',
            'odoo_queue_manager/static/src/js/queue_process.js',
        ],
        'web.assets_backend': [
            'odoo_queue_manager/static/src/js/dashboard.js',
            'odoo_queue_manager/static/src/xml/queue_management_dashboard_template.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True
}
