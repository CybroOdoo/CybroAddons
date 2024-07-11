# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
    'name': 'Customer Credit Payment In Website',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': """Assign the credit amount from the website and the sales""",
    'description': 'This is a module used to assign the credit to the customer'
                   ' in the website and also from the sales.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'purchase',
                'product', 'website_sale', 'payment', 'payment_demo'
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/website_credit_payment_security.xml',
        'data/website_data.xml',
        'data/product_data.xml',
        'views/credit_amount_views.xml',
        'views/credit_details_views.xml',
        'views/credit_payment_views.xml',
        'views/sale_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/customer_credit_payment_website_templates.xml',
        'views/restrict_message_template.xml',
        'views/payment_demo_templates.xml',
        'views/payment_token_views.xml',
        'views/payment_transaction_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'customer_credit_payment_website/static/src/js/**/*',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/icon.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
