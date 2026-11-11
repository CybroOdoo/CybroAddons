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
"""Shared fixtures for the salon_management test-suite.

The module resolves its stages through their XML ids (``salon_stage_00`` to
``salon_stage_04``), so the tests do not depend on database ids. They need
the master data (stages, "Salon Service" product and "Salon Default
Customer" partner) and skip themselves when it is missing.
"""
import unittest
from datetime import datetime, timedelta

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class SalonCommon(AccountTestInvoicingCommon):
    """Base class providing chairs, services, users and helpers."""

    # Far in the future so the records never collide with demo data.
    BASE_TIME = datetime(2031, 3, 10, 9, 0, 0)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        # AccountTestInvoicingCommon runs as an accounting-only user: give it
        # the salon rights (and settings rights for res.config.settings).
        cls.env.user.group_ids |= (
            env.ref('salon_management.group_salon_manager')
            | env.ref('base.group_system')
        )
        stage_refs = ['salon_stage_00', 'salon_stage_01', 'salon_stage_02',
                      'salon_stage_03', 'salon_stage_04']
        cls.stages = env['salon.stage']
        for ref in stage_refs:
            stage = env.ref('salon_management.%s' % ref,
                            raise_if_not_found=False)
            if not stage:
                raise unittest.SkipTest("Salon demo data is not loaded")
            cls.stages |= stage
        (cls.stage_draft, cls.stage_open, cls.stage_invoiced,
         cls.stage_closed, cls.stage_cancel) = cls.stages

        cls.chair = env['salon.chair'].sudo().create({'date': cls.BASE_TIME})
        cls.chair2 = env['salon.chair'].sudo().create({'date': cls.BASE_TIME})
        cls.service_hair = env['salon.service'].sudo().create({
            'name': 'Hair Cut', 'price': 100.0, 'time_taken': 1.0})
        cls.service_nail = env['salon.service'].sudo().create({
            'name': 'Manicure', 'price': 50.0, 'time_taken': 0.5})
        cls.customer = env['res.partner'].create({'name': 'Salon Customer'})

        # Make invoicing work regardless of the chart of accounts installed.
        cls.salon_product = env['product.product'].search(
            [('name', '=', 'Salon Service')], limit=1)
        if not cls.salon_product:
            raise unittest.SkipTest("'Salon Service' demo product is not loaded")
        cls.revenue_account = cls.company_data['default_account_revenue']
        cls.salon_product.property_account_income_id = cls.revenue_account
        if not env['res.partner'].sudo().search(
                [('name', '=', 'Salon Default Customer')]):
            env['res.partner'].sudo().create({'name': 'Salon Default Customer'})

        # The module's sequences are created for the main company, but the
        # accounting test user works in a different one: make them shared.
        env['ir.sequence'].sudo().search([
            ('code', 'in', ['salon.order.sequence', 'salon_chair_sequence']),
        ]).write({'company_id': False})

        # Holidays normally come from demo data; fall back to own records
        # so the tests also work on a database created without demo data.
        cls.holiday_sunday = env.ref('salon_management.salon_holiday_01',
                                     raise_if_not_found=False)
        if not cls.holiday_sunday:
            cls.holiday_sunday = env['salon.holiday'].sudo().create(
                {'name': 'Sunday', 'holiday': True})
        cls.holiday_monday = env.ref('salon_management.salon_holiday_02',
                                     raise_if_not_found=False)
        if not cls.holiday_monday:
            cls.holiday_monday = env['salon.holiday'].sudo().create(
                {'name': 'Monday', 'holiday': False})

        cls.user_tz = 'Asia/Kolkata'
        env.user.tz = cls.user_tz

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @classmethod
    def at(cls, hours=0, days=0):
        """Datetime relative to BASE_TIME."""
        return cls.BASE_TIME + timedelta(hours=hours, days=days)

    def make_order(self, start=None, chair=None, services=None, **kw):
        """Create a draft salon order with one line per service."""
        services = services if services is not None else (
            self.service_hair | self.service_nail)
        vals = {
            'customer_name': 'Walk-in',
            'chair_id': (chair or self.chair).id,
            'start_time': start or self.at(),
            'order_line_ids': [(0, 0, {
                'service_id': s.id, 'price': s.price,
                'price_subtotal': s.price, 'time_taken': s.time_taken,
            }) for s in services],
        }
        vals.update(kw)
        return self.env['salon.order'].create(vals)

    def make_booking(self, time=None, chair=None, services=None, **kw):
        vals = {
            'name': 'Booking Customer',
            'email': 'customer@example.com',
            'phone': '123456',
            'chair_id': (chair or self.chair).id,
            'time': time or self.at(),
            'service_ids': [(6, 0, (services if services is not None
                                    else self.service_hair).ids)],
        }
        vals.update(kw)
        return self.env['salon.booking'].create(vals)
