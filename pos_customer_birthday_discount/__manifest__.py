# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahul C K (odoo@cybrosys.com)
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
    'name': "POS Birthday Discount",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Extra discount on customer birthday""",
    'description': """Customers get extra discount for their orders in POS in 
     odoo on their birthdate.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            '/pos_customer_birthday_discount/static/src/xml/ActionpadWidget.xml',
            '/pos_customer_birthday_discount/static/src/js/birthday_discount.js',
            '/pos_customer_birthday_discount/static/src/js/models.js',
            '/pos_customer_birthday_discount/static/src/xml/Orderline.xml',
            '/pos_customer_birthday_discount/static/src/js/ProductScreen.js'
        ]
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
