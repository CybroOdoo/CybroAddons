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
    'name': 'Point of Sale Stock Transfer',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'summary': "Allows to directly transfer the "
                   "stock from the current POS session",
    'description': "This module allows to transfer stock(incoming order, "
                  "delivery order, internal transfer & POS orders) "
                   "from the POS session.",
    'data': ['views/res_config_settings_views.xml'],
    'assets': {
        'point_of_sale.assets': [
            '/pos_stock_transfer/static/src/xml/stock_transfer_button.xml',
            '/pos_stock_transfer/static/src/xml/transfer_ref_popup.xml',
            '/pos_stock_transfer/static/src/xml/transfer_create_popup.xml',
            '/pos_stock_transfer/static/src/js/stock_transfer.js',
            '/pos_stock_transfer/static/src/js/transfer_create_popup.js',
            '/pos_stock_transfer/static/src/js/transfer_ref_popup.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
