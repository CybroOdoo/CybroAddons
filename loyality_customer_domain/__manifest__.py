#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Loyalty Customer Domain',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Restrict the rules of loyalty, promotion and discount programs to the customers of a domain.',
    'description': """
     Restrict the rules of your loyalty, promotion, coupon and discount
     programs to the customers you choose. Set a customer domain on a rule,
     next to its product conditions: the rule only applies to the sale
     orders of the customers matching the domain, and the program is not
     available to the other customers.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_loyalty', 'sale_management'],
    'data': [
        'views/loyalty_rule_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
