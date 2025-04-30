# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
    'name': 'All in One POS Kit',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'This module combines Different POS features',
    'description': 'This module combines Different POS features',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'point_of_sale', 'mrp', 'sale', 'account','web','stock'],
    'external_dependencies': {'python': ['twilio', 'pandas']},
    'data': [
        'security/all_in_one_pos_kit_security.xml',
        'security/ir.model.access.csv',
        'views/pos_report_views.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        'views/dashboard_views.xml',
        'views/product_template_views.xml',
        'views/res_users_views.xml',
        'views/product_product_views.xml',
        'views/pos_greetings_views.xml',
        'views/meals_planning_views.xml',
        'report/pos_order_report.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'web/static/lib/zxing-library/zxing-library.js',
            'all_in_one_pos_kit/static/src/advanced_receipt/js/payment.js',
            'all_in_one_pos_kit/static/src/custom_tip/js/PaymentScreen.js',
            'all_in_one_pos_kit/static/src/exchange_product/js/models.js',
            'all_in_one_pos_kit/static/src/exchange_product/js/AllOrderScreen.js',
            'all_in_one_pos_kit/static/src/exchange_product/js/OrderButton.js',
            'all_in_one_pos_kit/static/src/exchange_product/js/ExchangeOrder.js',
            'all_in_one_pos_kit/static/src/exchange_product/scss/pos.scss',
            'all_in_one_pos_kit/static/src/multi_barcode/js/search_bar.js',
            'all_in_one_pos_kit/static/src/multi_barcode/js/ProductsWidgetControlPanel.js',
            'all_in_one_pos_kit/static/src/multi_barcode/js/pos_scan.js',
            'all_in_one_pos_kit/static/src/order_item_count/js/*',
            'all_in_one_pos_kit/static/src/order_line_image/css/order_line_image.css',
            'all_in_one_pos_kit/static/src/pos_auto_lot/js/auto_lot.js',
            'all_in_one_pos_kit/static/src/pos_logo/js/pos_image_field.js',
            'all_in_one_pos_kit/static/src/pos_logo/js/pos_receipt_image.js',
            'all_in_one_pos_kit/static/src/pos_mrp_order/js/models.js',
            'all_in_one_pos_kit/static/src/product_creation/js/product_create_popup.js',
            'all_in_one_pos_kit/static/src/product_creation/js/product_create_button.js',
            'all_in_one_pos_kit/static/src/product_magnify_image/js/MagnifyProductPopup.js',
            'all_in_one_pos_kit/static/src/product_magnify_image/js/ProductScreen.js',
            'all_in_one_pos_kit/static/src/product_magnify_image/css/pos_magnify_image.css',
            'all_in_one_pos_kit/static/src/time_based_product/js/*',
            'all_in_one_pos_kit/static/src/age_restricted/js/*',
            'all_in_one_pos_kit/static/src/service_charge/js/service_charge_button.js',
            'all_in_one_pos_kit/static/src/age_restricted/js/age_restrict.js',
            'all_in_one_pos_kit/static/src/age_restricted/js/restrict_popup.js',
        ],
        'web.assets_backend': [
            'all_in_one_pos_kit/static/src/category_wise_receipt/js/Screens/ReceiptScreen/OrderReceipt.js',
            'all_in_one_pos_kit/static/src/delete_order_line/js/*',
            'all_in_one_pos_kit/static/src/dashboard/js/pos_dashboard.js',
            'all_in_one_pos_kit/static/src/dashboard/css/pos_dashboard.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
            'all_in_one_pos_kit/static/src/mass_edit/js/pos_mass_edit_popup.js',
            'all_in_one_pos_kit/static/src/mass_edit/js/pos_mass_edit_button.js',
            'all_in_one_pos_kit/static/src/pos_num_show_hide/js/pos_numpad.js',
            'all_in_one_pos_kit/static/src/pos_report/css/*',
            'all_in_one_pos_kit/static/src/pos_report/js/*',
        ],
        'web.assets_qweb': [
            'all_in_one_pos_kit/static/src/advanced_receipt/xml/order_receipt_templates.xml',
            'all_in_one_pos_kit/static/src/category_wise_receipt/xml/Screens/ReceiptScreen/OrderReceipt.xml',
            'all_in_one_pos_kit/static/src/custom_tip/xml/PaymentScreen.xml',
            'all_in_one_pos_kit/static/src/delete_order_line/xml/*',
            'all_in_one_pos_kit/static/src/dashboard/xml/pos_dashboard.xml',
            'all_in_one_pos_kit/static/src/exchange_product/xml/AllOrderScreen.xml',
            'all_in_one_pos_kit/static/src/exchange_product/xml/ExchangeOrder.xml',
            'all_in_one_pos_kit/static/src/exchange_product/xml/OrderButton.xml',
            'all_in_one_pos_kit/static/src/mass_edit/xml/pos_mass_edit_popup.xml',
            'all_in_one_pos_kit/static/src/mass_edit/xml/pos_mass_edit_button.xml',
            'all_in_one_pos_kit/static/src/order_item_count/xml/*',
            'all_in_one_pos_kit/static/src/order_line_image/xml/pos_order_line.xml',
            'all_in_one_pos_kit/static/src/pos_logo/xml/pos_screen_image_views.xml',
            'all_in_one_pos_kit/static/src/pos_logo/xml/pos_ticket_views.xml',
            'all_in_one_pos_kit/static/src/pos_num_show_hide/xml/pos.xml',
            'all_in_one_pos_kit/static/src/pos_report/xml/*',
            'all_in_one_pos_kit/static/src/product_creation/xml/product_create_button.xml',
            'all_in_one_pos_kit/static/src/product_creation/xml/product_create_popup.xml',
            'all_in_one_pos_kit/static/src/product_magnify_image/xml/*',
            'all_in_one_pos_kit/static/src/service_charge/xml/ServiceChargeButton.xml',
            'all_in_one_pos_kit/static/src/age_restricted/xml/restrict_popup.xml'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
