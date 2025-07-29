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
    'name': "POS Dashboard",
    'version': '18.0.1.0.1',
    'category': 'Point of Sale',
    'summary': """Detailed dashboard view for POS""",
    'description': """Customized POS dashboard view""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'point_of_sale', 'web'],
    'data': [
        'views/pos_order_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'dashboard_pos/static/src/xml/pos_dashboard.xml',
            'dashboard_pos/static/src/js/pos_dashboard.js',
            'dashboard_pos/static/src/css/pos_dashboard.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js'
        ],
    },
    'external_dependencies': {
        'python': ['pandas'],
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
