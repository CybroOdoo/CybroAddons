# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aysha Shalin(<https://www.cybrosys.com>)
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
    'name': 'POS Restaurant Dine-in/TakeAway',
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """This module will add the options for Dine-in 
    and Take away in Odoo POS.""",
    'description': """The POS user can make orders as Dine-in or Take 
    away and it will create separate tokens for Take away orders.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'point_of_sale', 'pos_restaurant', 'web'],
    'data': [
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_order_filter_views.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/Screens/ProductScreen/ControlButtons/TakeAway.xml',
        'static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
