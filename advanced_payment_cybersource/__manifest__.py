# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<odoo@cybrosys.com>)
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
    'name': 'Odoo CyberSource Payment Gateway',
    'version': '16.0.1.0.0',
    'category': 'Website,eCommerce ',
    'summary': """cybersource payment gateway as a payment provider in which
     is used pay the order through website.""",
     'description': """cybersource payment gateway as a payment provider in which 
     is used pay the order through website.It provides an easy and fast payment 
     processing through cybersource.""",
     'author': 'Cybrosys Techno Solutions',
     'company': 'Cybrosys Techno Solutions',
     'maintainer': 'Cybrosys Techno Solutions',
     'website': 'https://www.cybrosys.com',
     'depends': ['payment', 'website_sale'],
     'data': [
        'views/payment_templates.xml',
        'data/advanced_payment_cybersource_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_transaction_views.xml',
     ],
     'assets': {
        'web.assets_frontend': [
            '/advanced_payment_cybersource/static/src/js/payment_form.js',
        ],
     },
    'external_dependencies': {
        'python': ['cybersource-rest-client-python']
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
