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
    'version': '17.0.1.0.0',
    'category': 'Extra Tools ',
    'summary': """Odoo Dynamic Dashboard, Dynamic Dashboard, Odoo Dashboard, Dynamic Dashbaord, AI Dashboard, Odoo17 Dashboard, Dashboard, Odoo17, Configurable Dashboard""",
    'description': """Create Configurable Dashboard Dynamically to get the 
    information that are relevant to your business, department, 
    or a specific process or need, Dynamic Dashboard, Dashboard ,
    Dashboard Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
        'views/dashboard_menu_view.xml',
        'views/dynamic_block_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_dynamic_dashboard/static/src/js/**/*.js',
            'odoo_dynamic_dashboard/static/src/scss/**/*.scss',
            'odoo_dynamic_dashboard/static/src/xml/**/*.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}
