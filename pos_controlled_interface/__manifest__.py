# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.

#############################################################################
{
    'name': 'Controlled Point Of Sale',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Manager Can Control Discount For the POS.',
    'description': "Manager Can Control Discount For the POS. So the"
                   " POS users can't control the discount in POS",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_config_settings_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_controlled_interface/static/src/js/NumpadWidget.js',
        ],
    },
    'license': 'AGPL-3',
    'images': ["static/description/banner.jpg"],
    'installable': True,
    'auto_install': False,
    'application': False,
}
