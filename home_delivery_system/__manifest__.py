# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
    'name': 'Home Delivery system',
    'version': '16.0.1.0.0',
    'category': 'Website,Sales',
    'summary': """Home delivery system is to deliver the orders through a 
     delivery person and then the delivery person can make the payment at the time
     of delivery.""",
    'description': 'Home delivery system is used to deliver the orders through '
                   'a delivery person',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'stock', 'website', 'hr',
                'website_sale'],
    'data': [
        'security/home_delivery_system_security.xml',
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'data/mail_template_data.xml',
        'views/stock_picking_views.xml',
        'views/website_open_jobs_templates.xml',
        'views/broadcasted_order_templates.xml',
        'views/completed_order_templates.xml',
        'views/delivery_option_templates.xml',
        'views/delivery_templates.xml',
        'views/home_delivery_system_menus.xml',
        'wizards/delivery_person_reschedule_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'home_delivery_system/static/src/js/delivery_available.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,

}
