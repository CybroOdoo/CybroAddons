# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Activity Checklist",
    'version': '19.0.1.0.0',
    'category': 'Discuss',
    'summary': """Create, organize, and track to-do activities efficiently using Odoo 
    scheduled activities with prioritization and recurrence options""",
    'description': """This module enables users to create structured to-do lists, 
    assign priorities, and track progress seamlessly within the system. Activities can be 
    scheduled with deadlines, categorized, and monitored through intuitive Kanban and tree views.
    Key Features:
    - Create and manage general to-do activities directly from the activity menu
    - Set recurring activities for repetitive tasks
    - Assign priorities to activities for better task organization
    - Visual indicators to highlight overdue and due-today activities
    - Filter and group activities based on creator, due date, and other criteria
    - User-friendly Kanban and list views for quick task tracking
    - Automated scheduling. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'live_test_url': 'https://youtu.be/LGiDWPFdkbks',
    'depends': ['sale', 'mail'],
    'data': [
        'security/mail_activity_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/activity_general_data.xml',
        'views/mail_activity_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
