# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Pos Direct Kitchen Print',
    'version': "18.0.1.0.0",
    'category': 'Sales/Point of Sale',
    'summary': "Direct Cloud Printing for POS Kitchen Orders using PrintNode.",
    'description': """
        This module provides a seamless integration between Odoo Point of Sale and PrintNode 
        for direct cloud-based kitchen ticket printing. It eliminates the need for complex 
        local print server setups or browser-based printing limitations.
        Key Features:
        - **PrintNode Integration**: Easily sync available printers from your PrintNode 
          account using an API key.
        - **Kitchen Printer Configuration**: Map PrintNode printers to specific kitchen 
          stations.
        - **Smart Ticket Routing**: Automatically route order lines to different kitchen 
          printers based on product categories.
        - **Multi-POS Support**: Configure specific printers for different POS instances.
        - **Real-time Status**: Monitor printer connectivity and states directly within Odoo.
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_restaurant'],
    'external_dependencies': {'python': ['printnodeapi']},
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/pos_kitchen_printer_views.xml',
        'views/pos_kitchen_printer_menus.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_direct_kitchen_print/static/src/**/*',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
