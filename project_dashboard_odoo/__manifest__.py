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
    'name': 'Project Dashboard',
    'category': 'Productivity',
    'summary': 'Detailed Dashboard View for Project',
    'description': 'Detailed Dashboard View for Project',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
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
            'project_dashboard_odoo/static/src/css/lib/nv.d3.css',
            'project_dashboard_odoo/static/src/css/dashboard.css',
            "project_dashboard_odoo/static/src/js/dashboard.js",
            'project_dashboard_odoo/static/src/js/lib/d3.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
        ],
        'web.assets_qweb': [
            'project_dashboard_odoo/static/src/xml/dashboard.xml',

        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
