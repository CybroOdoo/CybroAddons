# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Combine many useful Point of Sale features in one module",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'point_of_sale', 'mrp', 'product_expiry', 'web', 'mail'],
    'data': [
        'security/all_in_one_pos_kit_security.xml',
        'security/ir.model.access.csv',
        'data/pos_config_data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_config_views.xml',
        'views/dashboard_views.xml',
        'views/product_template_views.xml',
        'views/res_users_views.xml',
        'views/product_product_views.xml',
        'views/pos_report_views.xml',
        'views/pos_greetings_views.xml',
        'views/meals_planning_views.xml',
        'report/all_in_one_pos_kit_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'all_in_one_pos_kit/static/src/order_line_image/css/order_line_image.css',
            'all_in_one_pos_kit/static/src/service_charge/js/*',
            'all_in_one_pos_kit/static/src/age_restricted/js/*',
            'all_in_one_pos_kit/static/src/multi_barcode/js/pos_scan.js',
            'all_in_one_pos_kit/static/src/delete_order_line/css/*',
            'all_in_one_pos_kit/static/src/delete_order_line/js/*',
            'all_in_one_pos_kit/static/src/custom_tip/js/PaymentScreen.js',
            'all_in_one_pos_kit/static/src/pos_mrp_order/js/*',
            'all_in_one_pos_kit/static/src/pos_num_show_hide/js/pos_numpad.js',
            'all_in_one_pos_kit/static/src/advanced_receipt/xml/OrderReceipt.xml',
            'all_in_one_pos_kit/static/src/order_line_image/js/pos_order_line.js',
            'all_in_one_pos_kit/static/src/time_based_product/js/pos_model_load.js',
            'all_in_one_pos_kit/static/src/time_based_product/js/product_card_props.js',
            'all_in_one_pos_kit/static/src/time_based_product/js/pos_planning.js',
            'all_in_one_pos_kit/static/src/order_item_count/js/*',
            'all_in_one_pos_kit/static/src/order_item_count/xml/*',
            'all_in_one_pos_kit/static/src/mass_edit/js/*',
            'all_in_one_pos_kit/static/src/mass_edit/xml/*',
            'all_in_one_pos_kit/static/src/control_buttons/css/*',
            'all_in_one_pos_kit/static/src/order_line_image/xml/pos_order_line.xml',
            'all_in_one_pos_kit/static/src/delete_order_line/xml/*',
            'all_in_one_pos_kit/static/src/create_product/js/*',
            'all_in_one_pos_kit/static/src/create_product/xml/*',
            'all_in_one_pos_kit/static/src/custom_tip/xml/PaymentScreen.xml',
            'all_in_one_pos_kit/static/src/pos_num_show_hide/xml/pos.xml',
            'all_in_one_pos_kit/static/src/pos_logo/css/*',
            'all_in_one_pos_kit/static/src/pos_logo/xml/*',
        ],
        'web.assets_backend': [
            'all_in_one_pos_kit/static/src/dashboard/css/pos_dashboard.css',
            'all_in_one_pos_kit/static/src/pos_report/css/*',
            'all_in_one_pos_kit/static/src/dashboard/xml/pos_dashboard.xml',
            'all_in_one_pos_kit/static/src/dashboard/js/pos_dashboard.js',
            'all_in_one_pos_kit/static/src/pos_report/js/PosReport.js',
            'all_in_one_pos_kit/static/src/pos_report/xml/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
