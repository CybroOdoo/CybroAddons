# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Pos Custom Tips',
    'version': '17.0.1.0.0',
    'summary': """To apply a fixed percentage of Tip""",
    'description': """To apply a fixed percentage of tip to orders.
     we set a tip percentage it will be applied to the orders""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Point Of Sale',
    'depends': ['point_of_sale', 'pos_sale',],
    'data': {
        'views/res_config_settings_views.xml',
    },
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_custom_percentage_tip_fixed/static/src/js/PaymentScreen.js',
            'pos_custom_percentage_tip_fixed/static/src/xml/PaymentScreen.xml',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
