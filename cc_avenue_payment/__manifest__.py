# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'CCAvenue Payment Acquirer',
    'version': '16.0.1.0.0',
    'category': 'eCommerce,Marketing',
    'summary': 'CCAvenue Payment Gateway For Website',
    'description': "This module enables seamless payments through CCAvenue, "
                   "ensuring secure and convenient online transactions.",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'images': ['static/description/banner.png'],
    'depends': ['payment', 'account', 'website_sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/cc_avenue_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'external_dependencies': {'python': ['pay_ccavenue']},
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
