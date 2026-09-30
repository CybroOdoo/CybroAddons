# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Odoo GitHub Integration',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Complete GitHub integration with Projects, Issues, Pull Requests, and Webhooks',
    'description': """
        This module provides comprehensive GitHub integration:
        * Repository management and synchronization
        * GitHub issues sync with Odoo project tasks
        * Pull request tracking and management
        * Commit tracking and developer activity
        * Real-time webhook integration
        * Code review workflow
        * Automated notifications and updates
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'project',
        'mail',
    ],
    'external_dependencies': {
        'python': [
            'requests',
            'PyGithub',
            'python-dateutil',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/github_data.xml',
        'wizard/github_branch_create_wizard.xml',
        'wizard/github_pull_request_wizard_views.xml',
        'views/github_config_views.xml',
        'views/github_dashboard_views.xml',
        'views/github_repository_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/github_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_git_hub_integration/static/src/css/github_dashboard.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
