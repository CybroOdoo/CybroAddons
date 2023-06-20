# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Project Dashboard',
    'category': 'Productivity, Project',
    'summary': """Project Dashboard For Odoo16 Community And Enterprise Edition""",
    'description': """In this dashboard user the Detailed information about 
     project, task, employee, hours recorded, total margin and total 
     sale orders.""",
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale_management',
        'project',
        'sale_timesheet',
    ],
    'data': [
        'views/dashboard_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'assets': {
        'web.assets_backend': [
            'project_dashboard_odoo/static/src/css/dashboard.css',
            "project_dashboard_odoo/static/src/js/dashboard.js",
            'project_dashboard_odoo/static/src/xml/dashboard.xml',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
