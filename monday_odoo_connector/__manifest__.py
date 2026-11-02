# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
{
    'name': "Monday.com Odoo Connector",
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': "Connect Odoo with Monday.com to import Users, Boards, Groups, Items, and Customers",
    'description': "The Monday.com Odoo Connector module allows you to connect your Monday.com account to Odoo and import Users, Boards, Groups, Items, and Customers from Monday.com into Odoo.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.access.csv',
        'wizard/monday_connector_views.xml',
        'views/monday_credential_views.xml',
        'views/monday_board_views.xml',
        'views/monday_group_views.xml',
        'views/monday_item_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/item_column_value_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
