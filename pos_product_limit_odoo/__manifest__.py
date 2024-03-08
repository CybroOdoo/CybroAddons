# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
    'name': 'Pos Product Limit Odoo',
    'version': '17.0.1.0.0',
    'summary': """Pos Product Limit Odoo which is used to limit the number of 
     products in the pos.""",
    'description': """This module is used to limit the number of product loads 
     into the pos session. User can limit the products.""",
    'category': "Point of Sale",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': ['views/pos_config_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_limit_odoo/static/src/js/productWidget.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False,
}
