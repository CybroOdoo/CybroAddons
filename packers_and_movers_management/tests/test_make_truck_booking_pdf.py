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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for make.truck.booking.pdf wizard."""
from datetime import timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMakeTruckBookingPdf(TransactionCase):
    """Test cases for make.truck.booking.pdf wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Wizard Partner'})
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Small Truck',
            'capacity': 1.0,
            'weight': 1500.0,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Brand X'})
        cls.truck = cls.env['fleet.vehicle.model'].create({
            'name': 'Mini Truck',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })
        cls.goods_type = cls.env['goods.type'].create({'name': 'Boxes'})
        cls.booking = cls.env['truck.booking'].create({
            'partner_id': cls.partner.id,
            'from_location': 'Point A',
            'to_location': 'Point B',
            'distance': 40.0,
            'truck_id': cls.truck.id,
            'goods_type_id': cls.goods_type.id,
            'date': fields.Date.today(),
        })

    def test_wizard_date_validation(self):
        """Test wizard raises ValidationError when from_date is after to_date."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'from_date': fields.Date.today() + timedelta(days=5),
            'to_date': fields.Date.today(),
        })
        with self.assertRaises(ValidationError):
            wizard.action_report_truck_booking()

    def test_wizard_no_records_raises(self):
        """Test wizard raises ValidationError when no records match filter."""
        other_partner = self.env['res.partner'].create({'name': 'Unused Partner'})
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': other_partner.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_report_truck_booking()

    def test_wizard_action_report_success(self):
        """Test wizard generates report action with filtered booking records."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': self.partner.id,
            'truck_id': self.truck.id,
            'goods_type_id': self.goods_type.id,
            'from_date': fields.Date.today() - timedelta(days=1),
            'to_date': fields.Date.today() + timedelta(days=1),
        })
        res = wizard.with_context(discard_logo_check=True).action_report_truck_booking()
        self.assertIn(res.get('type'), ('ir.actions.report', 'ir.actions.act_window'))
        data = res.get('data')
        if not data and res.get('type') == 'ir.actions.act_window':
            import json
            ctx = res.get('context', {})
            if isinstance(ctx, str):
                ctx = json.loads(ctx)
            report_action = ctx.get('report_action', {})
            data = report_action.get('data')
        if data:
            self.assertIn('report', data)
            self.assertTrue(len(data['report']) >= 1)
            self.assertEqual(data['report'][0]['reference_no'], self.booking.reference_no)
