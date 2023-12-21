# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (<https://www.cybrosys.com>)
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
    'name': 'Product Create Or Edit From Point of Sale',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Create or edit products directly from the Point'
               ' of Sale interface.',
    'description': 'This module allows users to create or edit products '
                   'directly from the Point of Sale (POS) interface.'
                   ' It provides a convenient way to manage products'
                   ' on the fly without navigating to the backend.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'pos_product_create_edit/static/src/js/*',
            'pos_product_create_edit/static/src/css/*',
        ],
        'web.assets_qweb': [
            'pos_product_create_edit/static/src/xml/*',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
