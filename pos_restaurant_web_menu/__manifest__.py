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
    'name': 'POS Restaurant Web Menu',
    'version': '16.0.1.0.1',
    'category': 'Point of Sale',
    'summary': 'This module help to view Pos Restaurant Website Menu',
    'description': """This module create pos restaurant website menu for 
     Restaurant and create new order from web and generate Qr code of POS App 
     that allows customers to view the menu on their smartphone.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['pos_restaurant'],
    'data': [
        'report/pos_restaurant_web_menu_reports.xml',
        'report/pos_restaurant_web_menu_report_templates.xml',
        'views/pos_restaurant_web_menu_templates.xml',
        'views/res_config_settings_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pos_restaurant_web_menu/static/src/css/pos_restaurant_web_menu.css',
            'pos_restaurant_web_menu/static/src/js/pos_restaurant_web_menu.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
