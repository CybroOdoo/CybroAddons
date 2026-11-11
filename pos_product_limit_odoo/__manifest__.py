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
    'name': 'POS Product Limit Odoo',
    'version': '20.0.1.0.0',
    'category': "Point of Sale",
    'summary': """Limit the number of products displayed in the POS session for optimized loading speed.""",
    'description': """This module allows you to configure a limit on the number of products loaded and displayed in the POS session, improving performance and screen responsiveness.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': ['views/pos_config_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_limit_odoo/static/src/js/product_widget.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
