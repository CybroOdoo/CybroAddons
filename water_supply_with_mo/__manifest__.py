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
    'name': "Water Supply With Manufacturing Order",
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': """Create water supply methods and generate manufacturing orders from water supply requests""",
    'description': """This module allows you to configure water supply methods and create manufacturing orders directly from water supply requests.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'mrp', 'stock'],
    'data': [
        'security/water_supply_with_mo_groups.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'views/water_supply_method_views.xml',
        'views/water_usage_places_views.xml',
        'views/water_usage_categories_views.xml',
        'views/water_supply_request_views.xml',
        'views/manufacturing_order_creation_views.xml',
        'views/mrp_production_views.xml',
        'views/water_supply_with_mo_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
