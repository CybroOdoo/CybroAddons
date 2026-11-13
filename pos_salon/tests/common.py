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
from odoo.tests.common import TransactionCase


class TestSalonCommon(TransactionCase):
    """Base test class providing common fixtures and setup for pos_salon tests."""

    __test__ = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Optimize test environment: disable mail tracking & noisy notifications
        cls.env = cls.env(context=dict(
            cls.env.context,
            tracking_disable=True,
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
        ))

        # Specialist partner
        cls.specialist_partner = cls.env['res.partner'].create({
            'name': 'Test Specialist Partner',
            'email': 'specialist@salon.test',
            'phone': '+1234567890',
        })

        # Regular customer partner
        cls.customer_partner = cls.env['res.partner'].create({
            'name': 'Test Customer Partner',
            'email': 'customer@salon.test',
            'phone': '+9876543210',
        })

        # Customer without phone
        cls.customer_no_phone = cls.env['res.partner'].create({
            'name': 'Customer Without Phone',
            'email': 'nophone@salon.test',
        })

        # Customer without email
        cls.customer_no_email = cls.env['res.partner'].create({
            'name': 'Customer Without Email',
            'phone': '+1122334455',
        })

        # Product amenities
        cls.amenity_spa = cls.env['product.product'].create({
            'name': 'Steam Spa Treatment',
            'type': 'service',
            'list_price': 30.0,
            'available_in_pos': True,
        })
        cls.amenity_massage = cls.env['product.product'].create({
            'name': 'Shoulder Massage',
            'type': 'service',
            'list_price': 20.0,
            'available_in_pos': True,
        })

        # POS configuration with salon features enabled
        pos_config_vals = {
            'name': 'Test Salon POS Configuration',
            'is_salon': True,
            'is_spa': True,
            'salon_seats': 3,
            'apply_commission': True,
            'commission_type': 'auto',
            'commission_percent': 10.0,
            'take_review': True,
            'show_appointments': True,
            'show_all_appointments': True,
            'specialist_ids': [(6, 0, [cls.specialist_partner.id])],
            'amenities_ids': [(6, 0, [cls.amenity_spa.id, cls.amenity_massage.id])],
        }

        # Borrow required journal/picking settings from existing pos.config if available
        existing_config = cls.env['pos.config'].search([], limit=1)
        if existing_config:
            for field in ['picking_type_id', 'journal_id', 'invoice_journal_id']:
                if field in existing_config._fields and existing_config[field]:
                    pos_config_vals[field] = existing_config[field].id
            if 'payment_method_ids' in existing_config._fields and existing_config.payment_method_ids:
                pos_config_vals['payment_method_ids'] = [(6, 0, existing_config.payment_method_ids.ids)]

        cls.pos_config = cls.env['pos.config'].create(pos_config_vals)
