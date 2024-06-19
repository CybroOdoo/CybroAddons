# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
    'name': 'Display Stock in POS | Restrict Out-of-Stock Products in POS',
    'version': '16.0.1.0.1',
    'category': 'Point of Sale',
    'summary': "Enhance your Point of Sale experience by preventing the "
               "ordering of out-of-stock products during your session",
    'description': "This module enables you to limit the ordering of "
                   "out-of-stock products in POS as well as display the "
                   "available quantity for each product (on-hand quantity "
                   "and virtual quantity).",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': ['views/res_config_settings_views.xml'],
    'assets': {
        'point_of_sale.assets': [
            '/pos_restrict_product_stock/static/src/css/display_stock.css',
            '/pos_restrict_product_stock/static/src/xml/ProductItem.xml',
            '/pos_restrict_product_stock/static/src/xml/RestrictStockPopup.xml',
            '/pos_restrict_product_stock/static/src/js/RestrictStockPopup.js',
            '/pos_restrict_product_stock/static/src/js/ProductScreen.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
