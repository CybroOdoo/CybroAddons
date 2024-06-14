# -*- coding: utf-8 -*-

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P(<https://www.cybrosys.com>)
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
    'name': 'Age Restricted Products POS ',
    'version': '17.0.1.0.0',
    'summary': 'This Module will help to restrict the age restricted products '
               'in pos.',
    'description': 'This module enhances Point of Sale system by allowing users'
                   ' to set age restrictions for specific products. It includes'
                   ' features to check the product during product selection and'
                   'display warnings if they are in age restricted',
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'product'],
    'data': [
        'views/age_restrict_product_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'age_restricted_product_pos/static/src/js/age_restrict.js',
            'age_restricted_product_pos/static/src/js/restrict_popup.js',
            'age_restricted_product_pos/static/src/xml/restrict_popup.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
