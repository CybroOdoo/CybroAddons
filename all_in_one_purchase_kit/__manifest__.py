# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
    'name': 'All In One Purchase Kit',
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'An integrated module offering streamlined purchase management',
    'description': 'Product Brand for products, Purchase Order Line View,'
                   'Company Currency Total in Purchase, Employee Purchase '
                   'Requisition, Purchase All In One Report Generator,'
                   'Previous Purchase Product Rates, Barcode scanning support'
                   ' for Purchase, Amount in Words in Invoice for Purchase Order,'
                   'Multiple Purchase Order Confirm And Cancel,Merge Same '
                   'Product Line, Product image in order-line,'
                   'Purchase discount from Purchase order line,'
                   'Product Recommendation',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr', 'stock', 'purchase'],
    'data': [
        'security/all_in_one_purchase_kit_groups.xml',
        'security/all_in_one_purchase_kit_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'views/employee_purchase_requisition_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/employee_purchase_requisition_action.xml',
        'views/product_brand_views.xml',
        'views/product_template_views.xml',
        'views/purchase_report_views.xml',
        'views/purchase_order_line_views.xml',
        'views/rfq_line_views.xml',
        'views/purchase_report.xml',
        'views/account_move_views.xml',
        'views/product_product_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_supplier_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_dashboard.xml',
        'report/purchase_order_report_templates.xml',
        'report/all_in_one_purchase_kit_report_views.xml',
        'report/purchase_requisition_templates.xml',
        'report/purchase_order_templates.xml',
        'report/dynamic_purchase_report_action.xml',
        'wizard/product_recommendation_views.xml',
        'views/all_in_one_purchase_kit_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_purchase_kit/static/src/js/purchase_report.js',
            'all_in_one_purchase_kit/static/src/js/PurchaseDashboard.js',
            'all_in_one_purchase_kit/static/src/js/purchaseTile.js',
            'all_in_one_purchase_kit/static/src/css/purchase_dashboard.css',
            'all_in_one_purchase_kit/static/src/xml/purchase_report_views.xml',
            'all_in_one_purchase_kit/static/src/xml/dasboard_templates.xml',
            'all_in_one_purchase_kit/static/src/xml/purchaseTile.xml',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
