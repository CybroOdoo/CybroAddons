# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
###################################################################################

{
    'name': "POS Discount Limit",
    'summary': """
        This module is used to limit the discount on pos product category and  
        also restrict the global discount for selected cashiers.""",
    'description': """
        This module is used to limit the discount on pos product category and 
        also restrict the global discount for selected cashiers.""",    
    'version': '14.0.1.0.0',
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Point of Sale',
    'depends': ['point_of_sale','hr'],
    'data': [
        'views/views.xml',
        'views/restrict_discount_view.xml',
        'views/assets.xml',
    ],

    'images':[
        'static/description/banner.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,

}