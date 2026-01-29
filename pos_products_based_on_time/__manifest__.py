# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ruksana P (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'POS HAPPY HOURS | POS TIME BASED PRODUCTS',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """  This module enables you to display time-based products in 
     POS. The item will vary as time goes on""",
    'description': """ With the help of this module, you can display time-based 
     products in POS. With time, the item will change. The product can be 
     mentioned by the user in the pos configuration. The user can specify the
     product there""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'mail'],
    'data': [
        'security/meals_planning_security.xml',
        'security/ir.model.access.csv',
        'views/meals_planning_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_products_based_on_time/static/src/js/pos_model_load.js',
            'pos_products_based_on_time/static/src/js/pos_planning.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
