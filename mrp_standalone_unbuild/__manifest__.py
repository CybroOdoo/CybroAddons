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
    'name': 'MRP Standalone Unbuild',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Standalone unbuild orders for manufacturing products',
    'description': """
        Process unbuild operations independently without requiring a manufacturing order.
        The module adds editable component lines to unbuild orders, supports BoM-based
        component generation, and preserves the standard Odoo unbuild behavior when a
        manufacturing order is selected.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mrp'],
    'data': [
        'security/ir.access.csv',
        'views/mrp_unbuild_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
