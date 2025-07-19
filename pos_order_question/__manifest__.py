# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'POS Order Questions',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add questions related to the product in the session.',
    'description': "This provides an option to add questions related to the "
                   "product in the session at time of ordering.It will help "
                   "you to customize ordering in POS.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/pos_orderline_views.xml',
    ],
     'assets': {
        'point_of_sale._assets_pos': [
            'pos_order_question/static/src/js/PosSession.js',
            'pos_order_question/static/src/js/Popups/OrderQuestionPopup.js',
            'pos_order_question/static/src/xml/Popups/OrderQuestionPopup.xml',
            'pos_order_question/static/src/js/Screens/ProductScreen/Orderline.js',
            'pos_order_question/static/src/xml/Screens/ProductScreen/Orderline.xml',
            'pos_order_question/static/src/css/Popups/OrderQuestionPopup.css',
            'pos_order_question/static/src/js/Screens/ProductScreen/pos_orderline.js',
            'pos_order_question/static/src/js/pos_order.js',
        ]},
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
