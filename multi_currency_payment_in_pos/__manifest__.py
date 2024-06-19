# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
{
    'name': "POS Multi Currency Payment",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "This module allows us to make payment in multiple "
                   "currencies in Odoo 16 POS module.",
    'description': "This module in Odoo 16 offers the "
                   "option to expand its capabilities, enabling companies "
                   "to take payments in different currencies. A variety of "
                   "adjustments and setups are required for the POS module "
                   "to be extended to support several currencies, enabling "
                   "businesses to perform transactions in various monetary "
                   "units without any issues.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'multi_currency_payment_in_pos/static/xml/multicurrency_templates.xml',
            'multi_currency_payment_in_pos/static/src/js/pos_models.js',
            'multi_currency_payment_in_pos/static/src/js/pos_multicurrency.js',
            'multi_currency_payment_in_pos/static/src/js/backend_order.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
