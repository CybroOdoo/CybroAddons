# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "POS Customer Feedback",
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Customer Feedback in PoS',
    'description': "This module enables the management of customer feedback in"
                   "Odoo. It provides functionality to handle customer feedback"
                   "in both ratings and comments, ensuring effective feedback"
                   "management. With this module, businesses can gather and"
                   "utilize valuable customer feedback to enhance their"
                   "products and services.",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_customer_feedback/static/src/xml/feedback_popup_template.xml',
            'pos_customer_feedback/static/src/js/feedback_popup.js',
            'pos_customer_feedback/static/src/xml/customer_feedback_template.xml',
            'pos_customer_feedback/static/src/js/customer_feedback.js',
            'pos_customer_feedback/static/src/js/order_summary.js',
            'pos_customer_feedback/static/src/xml/order_summary_template.xml',
            'pos_customer_feedback/static/src/css/customer_feedback.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
