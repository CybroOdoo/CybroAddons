# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
###############################################################################
{
    'name': "PoS Analytic Tag",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'To manage analytic tags in POS',
    'description': "This module assists in managing analytic tags in the "
                   "Point of Sale. It enables the use of analytic filters in" 
                   "reporting, facilitating analysis based on these tags.",
    'author': " Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'analytic', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_config_views.xml',
        'views/pos_session_views.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_analytic_tag/static/src/js/PosSession.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
