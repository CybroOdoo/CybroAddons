# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
#
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
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
    'name': "Web Pay Shipping Methods",
    'version': '19.0.1.0.0',
    'category': 'eCommerce',
    'summary': """Select shipping methods based on payment provider.""",
    'description': """The shipping methods assigned to a payment provider will
    only be available when selecting that provider during the website sale
    checkout process.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/website_sale_delivery_templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'web_pay_shipping_methods/static/src/js/PaymentForm.js',
            'web_pay_shipping_methods/static/src/js/DeliveryMethod.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
