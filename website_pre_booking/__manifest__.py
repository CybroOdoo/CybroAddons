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
    'name': 'Website Pre Booking',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Pre-book website products in Odoo 20.',
    'description': """Allow website customers to reserve products with quantity
        limits and optional dates. Customers can track bookings by
        reference, and staff can create a linked sale order from the
        backend.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'views/portal_views.xml',
        'views/website_prebook_views.xml',
        'views/website_sale_inherit.xml',
        'views/prebook_details_template.xml',
        'views/pre_booking_template.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_pre_booking/static/src/css/prebooking.css',
            'website_pre_booking/static/src/js/pre_booking.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
