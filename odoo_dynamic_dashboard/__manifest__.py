# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Odoo Dynamic Dashboard",
    'version': '18.0.1.0.1',
    'category': 'Productivity',
    'summary': """Odoo Dynamic Dashboard, Dynamic Dashboard, Odoo18, Odoo18 Dashboards, Dashboard with AI, AI Dashboard, Odoo Dashboard,Graph View,""",
    'description': """Create Configurable Odoo Dynamic Dashboard to get the 
    information that are relevant to your business, department, or a specific 
    process or need""",
    'live_test_url': 'https://www.youtube.com/watch?v=bSUashq4_D8',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'data/dashboard_theme_data.xml',
        'views/dashboard_views.xml',
        'views/dynamic_block_views.xml',
        'views/dashboard_menu_views.xml',
        'views/dashboard_theme_views.xml',
        'wizard/dashboard_mail_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js',
            'odoo_dynamic_dashboard/static/src/css/**/*.css',
            'odoo_dynamic_dashboard/static/src/scss/**/*.scss',
            'odoo_dynamic_dashboard/static/src/js/**/*.js',
            'odoo_dynamic_dashboard/static/src/xml/**/*.xml',
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
            'odoo_dynamic_dashboard/static/src/js/interact_min.js'
        ],
    },
    'images': ['static/description/banner.gif'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}



