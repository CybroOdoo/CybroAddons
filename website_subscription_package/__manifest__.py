# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
    'name': 'Website Subscription Package Management',
    'version': '17.0.1.0.1',
    'category': 'Website',
    'summary': 'Subscription Package Management Through website',
    'description': """This Module Create Subscription for A Product From 
     Website""",
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['subscription_package', 'website_sale'],
    'data': [
        'data/mail_template_data.xml',
        'views/subscription_package_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/portal_templates.xml',
        'views/website_product_subscription_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_subscription_package/static/src/js/website_sale.js',
            'website_subscription_package/static/src/js/subscription.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
