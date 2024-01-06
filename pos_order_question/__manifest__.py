# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
    'name': 'POS Order Questions',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add questions related to the product in the session.',
    'description': "This provides an option to add questions related to the "
                   "product in the session at time of ordering.It will help "
                   "you to customize ordering in POS.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_order_question/static/src/css/Popups/OrderQuestionPopup.css',
            'pos_order_question/static/src/js/PosSession.js',
            'pos_order_question/static/src/js/Screens/ProductScreen/Orderline.js',
            'pos_order_question/static/src/js/Popups/OrderQuestionPopup.js',
            'pos_order_question/static/src/js/Screens/ReceiptScreen/OrderReceipt.js',
            'pos_order_question/static/src/xml/Screens/ProductScreen/Orderline.xml',
            'pos_order_question/static/src/xml/Popups/OrderQuestionPopup.xml',
            'pos_order_question/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
