# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul  (odoo@cybrosys.com)
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
    'name': 'App Category View',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Make Apps category wise as you need',
    'description': 'The "App Category View" app allows users to efficiently'
                   'categorize and organize the apps based on specific '
                   'category.',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solution',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': ['base', 'web_enterprise'],
    'data': ['security/ir.model.access.csv',
             'data/ir_sequence.xml',
             'views/ir_app_category_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'app_category_view/static/src/xml/home_dashboard_templates.xml',
            'app_category_view/static/src/js/home_menu.js',
            'app_category_view/static/src/js/app_move.js',
            'app_category_view/static/src/css/home_dashboard.css']},
    'images': [
        'static/description/banner.jpg'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
