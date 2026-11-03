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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Delivery Slot',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': "Time slot selection for deliveries",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_stock', 'website_sale'],
    'data': [
        'security/ir.access.csv',
        'views/delivery_slot_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/slot_time_views.xml',
        'views/website_delivery_slot_templates.xml',
        'views/website_slot_time_templates.xml',
    ],
    'demo': [
        'demo/slot_time_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'delivery_slot/static/src/js/delivery_slot.js',
            'delivery_slot/static/src/js/slot_time.js',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
