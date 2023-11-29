# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
    'name': 'Advanced POS Reports',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Generates various reports from POS screen and reporting 
     menu""",
    'description': """Generates various reports like, top 
     selling products / categories / customers report, ongoing sessions report,
     posted sessions report under reporting menu.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/advanced_pos_reports_wizard.xml',
        'wizard/pos_sale_ongoing_views.xml',
        'wizard/pos_sale_posted_views.xml',
        'wizard/pos_sale_top_selling_views.xml',
        'report/advanced_pos_reports.xml',
        'report/pos_ongoing_session_templates.xml',
        'report/pos_posted_session_templates.xml',
        'report/pos_top_selling_categories_templates.xml',
        'report/pos_top_selling_customers_templates.xml',
        'report/pos_top_selling_products_templates.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'advanced_pos_reports/static/src/js/Category.js',
            'advanced_pos_reports/static/src/js/CategoryPopup.js',
            'advanced_pos_reports/static/src/js/CategoryReceipt.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen.js',
            'advanced_pos_reports/static/src/xml/Category_templates.xml',
            'advanced_pos_reports/static/src/xml/Popup_templates.xml',
            'advanced_pos_reports/static/src/xml/CategoryReceipt_templates.xml',
            'advanced_pos_reports/static/src/xml/ReceiptScreen_templates.xml',
            'advanced_pos_reports/static/src/js/Location.js',
            'advanced_pos_reports/static/src/js/LocationPopup.js',
            'advanced_pos_reports/static/src/js/LocationReceipt.js',
            'advanced_pos_reports/static/src/js/LocationReceiptScreen.js',
            'advanced_pos_reports/static/src/xml/Location_templates.xml',
            'advanced_pos_reports/static/src/xml/LocationPopup_templates.xml',
            'advanced_pos_reports/static/src/xml/LocationReceipt_templates.xml',
            'advanced_pos_reports/static/src/xml/LocationReceiptScreen_templates.xml',
            'advanced_pos_reports/static/src/js/Order.js',
            'advanced_pos_reports/static/src/js/OrderPopup.js',
            'advanced_pos_reports/static/src/js/OrderReceipt.js',
            'advanced_pos_reports/static/src/js/OrderReceiptScreen.js',
            'advanced_pos_reports/static/src/xml/Order_templates.xml',
            'advanced_pos_reports/static/src/xml/OrderPopup_templates.xml',
            'advanced_pos_reports/static/src/xml/OrderReceipt_templates.xml',
            'advanced_pos_reports/static/src/xml/OrderReceiptScreen_templates.xml',
            'advanced_pos_reports/static/src/js/Payment.js',
            'advanced_pos_reports/static/src/js/PaymentPopup.js',
            'advanced_pos_reports/static/src/js/PaymentReceipt.js',
            'advanced_pos_reports/static/src/js/PaymentReceiptScreen.js',
            'advanced_pos_reports/static/src/xml/Payment_templates.xml',
            'advanced_pos_reports/static/src/xml/PaymentPopup_templates.xml',
            'advanced_pos_reports/static/src/xml/PaymentReceipt_templates.xml',
            'advanced_pos_reports/static/src/xml/PaymentReceiptScreen_templates.xml',
            'advanced_pos_reports/static/src/js/Product.js',
            'advanced_pos_reports/static/src/js/ProductPopup.js',
            'advanced_pos_reports/static/src/js/ProductReceipt.js',
            'advanced_pos_reports/static/src/js/ProductReceiptScreen.js',
            'advanced_pos_reports/static/src/xml/Product_templates.xml',
            'advanced_pos_reports/static/src/xml/ProductPopup_templates.xml',
            'advanced_pos_reports/static/src/xml/ProductReceipt_templates.xml',
            'advanced_pos_reports/static/src/xml/ProductReceiptScreen_templates.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
