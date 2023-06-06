# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Purchase Down Payment',
    'version': '16.0.1.0.0',
    'summary': """Down payment with purchase order""",
    'description': """"This module provides easy feature to register down payment against the purchase order. 
                       User will be able to register downpayment in percentage and amount that would deduct 
                       from vendor bill.""",
    'category': 'Purchase',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'purchase', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/purchase_order_advance_payment_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
