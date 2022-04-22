# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

{
    'name': 'Advanced POS Reports',
    'version': '15.0.1.0.0',
    'summary': """Generates Various Reports From POS Screen and From Reporting Menu""",
    'description': """Generates various reports like Sales summary, top selling products / categories / 
                      customers report, ongoing sessions report, posted sessions report under reporting menu, """,
    'category': 'Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['point_of_sale', 'pos_sale'],
    'website': 'https://www.cybrosys.com',
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_sale_details.xml',
        'wizard/top_selling.xml',
        'wizard/ongoing_session.xml',
        'wizard/posted_session.xml',
        'wizard/top_selling.xml',
        'views/reports.xml',
        'views/report_pos_saledetails.xml',
        'views/report_pos_posted_session.xml',
        'views/report_pos_ongoing_session.xml',
        'views/report_pos_top_selling_products.xml',
        'views/report_pos_top_selling_categories.xml',
        'views/report_pos_top_selling_customers.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'advanced_pos_reports/static/src/js/ControlButtons/PaymentSummaryButton.js',
            'advanced_pos_reports/static/src/js/ControlButtons/ProductSummaryButton.js',
            'advanced_pos_reports/static/src/js/ControlButtons/CategorySummaryButton.js',
            'advanced_pos_reports/static/src/js/ControlButtons/LocationSummaryButton.js',
            'advanced_pos_reports/static/src/js/ControlButtons/OrderSummaryButton.js',
            'advanced_pos_reports/static/src/js/ControlButtons/SessionSummaryButton.js',
            'advanced_pos_reports/static/src/js/Popups/LocationSummaryPopup.js',
            'advanced_pos_reports/static/src/js/Popups/CategorySummaryPopup.js',
            'advanced_pos_reports/static/src/js/Popups/OrderSummaryPopup.js',
            'advanced_pos_reports/static/src/js/Popups/PaymentSummaryPopup.js',
            'advanced_pos_reports/static/src/js/Popups/ProductSummaryPopup.js',
            'advanced_pos_reports/static/src/js/Popups/SessionSummaryPopup.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/LocationSummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/CategorySummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/OrderSummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/PaymentSummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/ProductSummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/ReceiptScreen/SessionSummaryReceiptScreen.js',
            'advanced_pos_reports/static/src/js/Receipts/OrderSummaryReceipt.js',
            'advanced_pos_reports/static/src/js/Receipts/PaymentSummaryReceipt.js',
            'advanced_pos_reports/static/src/js/Receipts/ProductSummaryReceipt.js',
            'advanced_pos_reports/static/src/js/Receipts/CategorySummaryReceipt.js',
            'advanced_pos_reports/static/src/js/Receipts/SessionSummaryReceipt.js',
            'advanced_pos_reports/static/src/js/Receipts/LocationSummaryReceipt.js',
            'advanced_pos_reports/static/src/css/advanced_report.css',
        ],
        'web.assets_qweb': [
            'advanced_pos_reports/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
