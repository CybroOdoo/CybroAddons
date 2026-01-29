# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'One Page Checkout',
    'version': '15.0.1.0.0',
    'category': 'eCommerce',
    'summary': """
        Simplifies ecommerce checkout by condensing it into a single,
        user-friendly page.
        """,
    'description': """
        Condenses the entire ecommerce checkout process into a single,
        user-friendly page, simplifying the steps and enhancing the user
        experience.
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.jpg'],
    'depends': ['website', 'website_sale'],
    'data': [
        'views/address_column_templates.xml',
        'views/address_form_templates.xml',
        'views/extra_info_templates.xml',
        'views/payment_templates.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'one_page_checkout/static/src/css/style.css',
            'one_page_checkout/static/src/js/website_sale.js',
            'one_page_checkout/static/src/js/checkout_form.js',
            'one_page_checkout/static/src/js/website_sale_delivery.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
