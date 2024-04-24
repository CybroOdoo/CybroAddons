# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Product Data Feed Generation',
    'version': '17.0.1.0.0',
    'category': 'eCommerce',
    'summary': 'Help to create the catalog for promoting your sale',
    'description': 'Using this module we have to promote and market our sales'
                   ' through facebook and instagram for using the catalog of '
                   'our product. Many of the businesses sell or advertise  '
                   'their product  through  facebook and instagram. So they'
                   ' need a catalog that contains the information about your '
                   'products. In this module generate the product data feed '
                   'file for the facebook commerce manager in automatic '
                   'mode(by URL). After adding the data feed URL on facebook '
                   'you will be able to promote your product in sale channels ,'
                   ' on facebook shops, instagram shopping, with dynamic ads,'
                   ' and more.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'product', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_data_feed_views.xml',
        'views/product_data_feed_columns_views.xml',
        'views/field_column_value_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
