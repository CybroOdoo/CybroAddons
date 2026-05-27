# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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

###############################################################################
{
    'name': 'Point of Sale Stock Transfer',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Allows to Directly Transfer the Stock From the Current POS"
               " Session",
    'description': "This module allows for the immediate movement of stock "
                   "within the same point-of-sale (POS) session.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': ['views/res_config_settings_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'stock_transfer_in_pos/static/src/app/**/*',
            'stock_transfer_in_pos/static/src/overrides/components/control_buttons/control_buttons.xml',
            'stock_transfer_in_pos/static/src/overrides/components/control_buttons/control_buttons.js',
                    ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
