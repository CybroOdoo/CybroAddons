# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjitha V(odoo@cybrosys.com)
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
    'name': 'Website Customer Note',
    'version': '16.0.1.0.0',
    'category': 'Ecommerce',
    'summary': 'This Module Helps to Add Customer Note on Advance payment Screen .',
    'description': """This Module Helps to Add Customer Note on Advance payment Screen.And it will display on the sale order form view""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base','sale_management', 'website_sale'],
    'data': [
        'views/website_sale_inherit_view.xml',
        'views/sale_order_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_customer_note/static/js/pay_now_button.js'
        ],
    },
    'images': ['static/description/assets/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
