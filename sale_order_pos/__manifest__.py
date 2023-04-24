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
    'name': "POS Sale order ",
    'version': '15.0.1.0.0',
    'summary': """
        Create Sales order from POS. """,
    'description': """
        Creating Sales order from Point of Sale with a single click. 
    """,
    'category': 'Point of Sale',
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'maintainer': "Cybrosys Techno Solutions",
    'depends': ['base', 'point_of_sale', 'sale_management'],
    'assets': {
        'web.assets_backend': [
            'sale_order_pos/static/src/js/sale_order_button.js',
        ],
        'web.assets_qweb': [
             'sale_order_pos/static/src/xml/sale_order_button.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
