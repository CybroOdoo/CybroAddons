# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Delivery Slot',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': "Time slot selection for deliveries",
    'description': """This module helps to choose a different delivery date 
    and time for each product in the order line. Multiple deliveries and 
    corresponding delivery slots are created for each line in the sale order,
    based on the chosen date and slot.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'stock', 'account', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/slot_time_data.xml',
        'views/delivery_slot_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/slot_time_views.xml',
        'views/website_delivery_slot_templates.xml',
        'views/website_slot_time_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'delivery_slot/static/src/js/delivery_slot.js',
            'delivery_slot/static/src/js/slot_time.js',
            'delivery_slot/static/src/js/website_sale_utils.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'licence': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
