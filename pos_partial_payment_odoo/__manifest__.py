# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.info)
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
################################################################################
{
    'name': 'POS Partial Payment',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Simplify Payments with Partial Payment in Odoo POS",
    'description': "In Odoo POS, partial payments allow customers to pay for "
                   "their purchases in multiple installments, making it "
                   "easier for customers to split payments or pay later. This "
                   "feature is especially helpful for businesses dealing with "
                   "larger orders or customers who prefer flexibility in "
                   "their payment options.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_partial_payment_odoo/static/src/js/payment_screen.js',
            'pos_partial_payment_odoo/static/src/js/models.js',
            'pos_partial_payment_odoo/static/src/js/ticket_screen.js',

        ], 'web.assets_qweb': [
            'pos_partial_payment_odoo/static/src/xml/payment_screen.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

