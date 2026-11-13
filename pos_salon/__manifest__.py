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
    'name': 'POS Salon Management',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Manage salon appointments and services from Point of Sale',
    'description': """Salon and Spa POS extends Odoo Point of Sale with a complete salon workflow.
                    Staff can book scheduled appointments and walk-ins, assign specialists and
                    amenities, manage seats and time slots, take payment through the POS, track
                    specialist commission, and collect customer reviews.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'mail'],
    'data': [
        'security/salon_booking_security.xml',
        'security/ir.model.access.csv',
        'data/salon_product_data.xml',
        'data/mail_template_data.xml',
        'views/salon_booking_views.xml',
        'views/salon_review_templates.xml',
        'views/pos_order_views.xml',
        'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_salon/static/src/app/utils/salon_currency.js',
            'pos_salon/static/src/app/utils/salon_date.js',
            'pos_salon/static/src/app/index.js',
            'pos_salon/static/src/app/navbar/navbar.xml',
            'pos_salon/static/src/app/hooks/salon_booking_actions.js',
            'pos_salon/static/src/app/components/salon_customer/salon_customer.js',
            'pos_salon/static/src/app/components/salon_booking_summary/salon_booking_summary.js',
            'pos_salon/static/src/app/components/salon_commission_popup/salon_commission_popup.js',
            'pos_salon/static/src/app/screens/salon_screen/salon_screen.js',
            'pos_salon/static/src/app/screens/book_appointment/book_appointment.js',
            'pos_salon/static/src/app/screens/slot_booking/slot_booking.js',
            'pos_salon/static/src/app/screens/show_appointments/show_appointments.js',
            'pos_salon/static/src/app/screens/track_all_appointments/track_all_appointments.js',
            'pos_salon/static/src/app/screens/commission/commission.js',
            'pos_salon/static/src/app/screens/walkin_appointments/walk_in_appointments.js',
            'pos_salon/static/src/app/screens/running_appointments/running_appointments.js',
            'pos_salon/static/src/app/components/salon_customer/salon_customer.xml',
            'pos_salon/static/src/app/components/salon_booking_summary/salon_booking_summary.xml',
            'pos_salon/static/src/app/components/salon_commission_popup/salon_commission_popup.xml',
            'pos_salon/static/src/app/screens/salon_screen/salon_screen.xml',
            'pos_salon/static/src/app/screens/book_appointment/book_appointment.xml',
            'pos_salon/static/src/app/screens/slot_booking/slot_booking.xml',
            'pos_salon/static/src/app/screens/show_appointments/show_appointments.xml',
            'pos_salon/static/src/app/screens/track_all_appointments/track_all_appointments.xml',
            'pos_salon/static/src/app/screens/commission/commission.xml',
            'pos_salon/static/src/app/screens/walkin_appointments/walk_in_appointments.xml',
            'pos_salon/static/src/app/screens/running_appointments/running_appointments.xml',
            'pos_salon/static/src/css/salon_screen.css',
            'pos_salon/static/src/css/book_appointment.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
