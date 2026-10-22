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
    'name': "Cancel Landed Cost",
    'version': "20.0.1.0.0",
    'category': 'Inventory/Inventory',
    'summary': 'This module helps to cancel landed costs',
    'description': 'This module helps to cancel Landed Costs and allows you '
                   'to cancel multiple Landed Costs from the tree view. There '
                   'are three ways in which you can cancel the Landed Costs: '
                   'Cancel Only, Cancel and Reset to Draft, Cancel and Delete.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_landed_costs', 'stock_account'],
    'data': [
        'security/cancel_landed_cost_odoo_groups.xml',
        'data/stock_landed_cost_data.xml',
        'views/stock_landed_cost_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
