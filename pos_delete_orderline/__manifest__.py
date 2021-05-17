# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Remove Order Line In POS ",
    'summary': """
        Remove Individual Orderlines In Point Of Sale. """,
    'description': """
        Remove each lines from selected order by simply clicking X button or clear all order with a single click. 
    """,
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'maintainer': "Cybrosys Techno Solutions",
    'category': 'Point of Sale',
    'version': '14.0.1.0.0',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/views.xml',
    ],
    'qweb': ['static/src/xml/clear_button.xml',
             'static/src/xml/clear_order_line.xml',
             ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
