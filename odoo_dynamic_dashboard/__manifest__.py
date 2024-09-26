# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Odoo Dynamic Dashboard",
    'version': '17.0.2.0.1',
    'category': 'Productivity',
    'summary': """Create Configurable Dashboards Easily""",
    'description': """Odoo Dynamic Dashboard, Dynamic Dashboard, Odoo Dashboard, Web Dynamic Dashboard, Dashboard with AI, Analytic Dashboard, AI Dashboard, Odoo17 Dashboard, Responsive Dashboard, Odoo17, Dashboard""",
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
            'odoo_dynamic_dashboard/static/src/css/**/*.css',
            'odoo_dynamic_dashboard/static/src/scss/**/*.scss',
            'odoo_dynamic_dashboard/static/src/js/**/*.js',
            'odoo_dynamic_dashboard/static/src/xml/**/*.xml',
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
            'odoo_dynamic_dashboard/static/lib/js/interactjs.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}



