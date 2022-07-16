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
    'name': "Product Stock Alert",
    'version': '14.0.1.0.0',
    'summary': """Product Stock Alert""",
    "category": 'Inventory',
    'description': """Product Stock Alert""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'stock', 'point_of_sale', 'product'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml'
    ],
    'qweb': [
        'static/src/xml/alert_tag_js.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'application': True
}
