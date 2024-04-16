# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Advanced Project Management System",
    "version": "17.0.1.0.0",
    "category": "Project",
    "summary": "Advanced Project Management System can handle projects,"
    "tasks, due dates, checklists",
    "description": """Advanced Project Management System designed to streamline 
    every aspect of your projects. From handling projects and tasks to managing 
    due dates and checklists, this all-in-one solution simplifies project and 
    task management for you.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['project', 'hr_timesheet'],
    'data': [
        'security/advanced_project_management_system_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'data/ir_actions_server_data.xml',
        'data/ir_sequence_data.xml',
        'views/project_milestone_views.xml',
        'views/res_config_settings_views.xml',
        'views/project_checklist_views.xml',
        'views/project_task_checklist_views.xml',
        'views/project_task_views.xml',
        'views/project_task_checklist_template_views.xml',
        'views/project_checklist_template_views.xml',
        'views/project_category_views.xml',
        'views/project_project_views.xml',
        'views/ir_attachment_views.xml',
        'views/project_issue_views.xml',
        'report/project_project_template.xml',
        'report/project_task_template.xml',
        'report/ir_action_report.xml',
        'report/project_task_burnup_chart_report_views.xml',
        'report/project_task_velocity_chart_report_views.xml',
        'wizard/project_task_checklist_import_views.xml',
        'wizard/project_stage_update_views.xml',
        'wizard/project_task_mass_update_views.xml',
        'wizard/project_shortcut_views.xml'
    ],
    'assets': {
        'web.assets_backend': {
            'advanced_project_management_system/static/src/scss/style.scss',
            'advanced_project_management_system/static/src/js/burnup_chart_search_model.js',
            'advanced_project_management_system/static/src/js/burnup_chart_model.js',
            'advanced_project_management_system/static/src/js/burnup_chart_view.js',
            'advanced_project_management_system/static/src/xml/burnup_chart_view.xml',
            'advanced_project_management_system/static/src/xml/chatter_templates.xml',
            'advanced_project_management_system/static/src/js/composer_patch.js',
            'advanced_project_management_system/static/src/js/velocity_chart_model.js',
            'advanced_project_management_system/static/src/js/velocity_chart_search_model.js',
            'advanced_project_management_system/static/src/js/velocity_chart_view.js',
            'advanced_project_management_system/static/src/xml/velocity_chart_view.xml',
        },
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
