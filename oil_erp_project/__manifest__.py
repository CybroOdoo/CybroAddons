# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Oil & Gas Project',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Project Management',
    'summary': 'Project module customisation for Oil and Gas ERP',
    'description': """
Project customizations for Oil & Gas industry:
- Auto-create Project on Oil Reservoir creation
- Auto-create Storage Location on Project creation
- Rename Tasks to Wells
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'project',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/production_wizard_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/project_task_type_views.xml',
        'views/project_task_reporting_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'create_task_stages',
}
