# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
{
    "name": "POS Multi Currency Pricelist",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Use POS pricelists with different currencies and show the selected currency in the POS UI.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "depends": ["point_of_sale"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_multi_currency_pricelist/static/src/app/utils/currency_helpers.js",
            "pos_multi_currency_pricelist/static/src/app/store/pos_store_patch.js",
            "pos_multi_currency_pricelist/static/src/app/utils/contextual_utils_service_patch.js",
            "pos_multi_currency_pricelist/static/src/app/store/product_patch.js",
            "pos_multi_currency_pricelist/static/src/app/store/payment_patch.js",
            "pos_multi_currency_pricelist/static/src/app/store/orderline_patch.js",
            "pos_multi_currency_pricelist/static/src/app/store/order_patch.js",
            "pos_multi_currency_pricelist/static/src/app/screens/payment_screen_patch.js",
            "pos_multi_currency_pricelist/static/src/app/screens/product_screen/order_summary/order_summary_patch.js",
            "pos_multi_currency_pricelist/static/src/app/screens/product_screen/order_summary/order_summary_patch.xml",
            "pos_multi_currency_pricelist/static/src/app/screens/product_screen/product_info_popup/product_info_popup_patch.js",
            "pos_multi_currency_pricelist/static/src/app/screens/product_screen/product_info_popup/product_info_popup_patch.xml",
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    "installable": True,
    'auto_install': False,
    "application": False,

    'description': 'A longer description of what this module does.',
}
