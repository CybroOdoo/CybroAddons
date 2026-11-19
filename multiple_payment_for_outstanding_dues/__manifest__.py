# -*- coding: utf-8 -*-
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
    'name': 'Multiple Payment For Outstanding Dues',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': """Pay multiple outstanding customer invoices at once, Customer Due Amount, Odoo20 Due Payment""",
    'description': """
     This module shows the total outstanding due of each customer on the
     customer form and lets you register the payment for one or more due
     invoices at once, from the Due Statements smart button.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account'],
    'data': [
        'security/ir.access.csv',
        'data/ir_actions_server_data.xml',
        'views/account_move_line_views.xml',
        'views/res_partner_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
