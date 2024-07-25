# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.info)
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
    'name': "Volunteers and Donors Management",
    'version': "17.0.1.0.0",
    'category': 'Extra Tools',
    'summary': "The app helps manage volunteers and donors in Odoo, allowing "
               "assign volunteers and donors in Project and CRM ",
    'description': "This app allows you to manage your volunteers and donors "
                   "in Odoo and allows you to create projects and tasks with "
                   "volunteers and activities volunteers . It also allows you"
                   "to select volunteer and donor details on CRM of lead / "
                   "pipelines.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['crm', 'hr', 'project', 'sale_management', 'sale_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'security/volunteers_donors_management_groups.xml',
        'report/project_reports.xml',
        'report/project_report_templates.xml',
        'views/res_partner_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/crm_lead_views.xml',
        'views/volunteer_type_views.xml',
        'views/volunteer_skill_views.xml',
        'views/donor_type_views.xml',
        'views/volunteers_and_donors_management_menu.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

