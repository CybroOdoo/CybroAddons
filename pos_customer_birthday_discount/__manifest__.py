# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Pos Birthday Discount",
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Extra discount on customer birthday""",
    'description': """Customers get extra discount for their orders in POS 
    in odoo on their birth date.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/pos_config_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_customer_birthday_discount/static/src/js/ActionpadWidget.js',
            'pos_customer_birthday_discount/static/src/js/Orderline.js',
            'pos_customer_birthday_discount/static/src/js/PaymentScreen.js',
            'pos_customer_birthday_discount/static/src/js/ProductScreenInherit.js'
        ],
        'web.assets_qweb': [
            'pos_customer_birthday_discount/static/src/xml/ActionpadWidgetInherit.xml',
            'pos_customer_birthday_discount/static/src/xml/OrderlineInherit.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
