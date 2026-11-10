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
"""Test suite for table.reservation model and all its methods."""
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.addons.base.models.ir_config_parameter import IrConfig_Parameter


def _attach_compat_params(model_cls):
    if not hasattr(model_cls, 'get_param'):
        def _get_param(self, key, default=False):
            val = self.get_str(key, default=None)
            if val is None or val is False or val == '':
                return default
            return val
        model_cls.get_param = _get_param
    if not hasattr(model_cls, 'set_param'):
        def _set_param(self, key, value):
            return self.set_str(key, str(value) if value is not False and value is not None else '')
        model_cls.set_param = _set_param


_attach_compat_params(IrConfig_Parameter)


@tagged('post_install', '-at_install')
class TestTableReservation(TransactionCase):
    """Test all methods and validations of table.reservation model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _attach_compat_params(type(cls.env['ir.config_parameter']))
        _attach_compat_params(IrConfig_Parameter)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Reservation Tester',
            'email': 'tester@example.com',
        })
        cls.floor = cls.env['restaurant.floor'].create({
            'name': 'Indoor Hall',
        })
        cls.table1 = cls.env['restaurant.table'].create({
            'table_number': 1,
            'floor_id': cls.floor.id,
            'rate': 25.0,
            'seats': 2,
        })
        cls.table2 = cls.env['restaurant.table'].create({
            'table_number': 2,
            'floor_id': cls.floor.id,
            'rate': 50.0,
            'seats': 4,
        })
        cls.today = date.today()
        cls.tomorrow = cls.today + timedelta(days=1)

    def test_create_and_sequence(self):
        """Test reservation creation and automatic sequence assignment."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '18:00',
            'ending_at': '20:00',
        })
        self.assertTrue(reservation.sequence)
        self.assertNotEqual(reservation.sequence, 'New')
        self.assertEqual(reservation.state, 'draft')

    def test_compute_lead_time(self):
        """Test _compute_lead_time when parameter is enabled."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.reservation_lead_time', 2.0)

        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '18:00',
            'ending_at': '20:00',
            'lead_time': 0.0,
            'lead_time_computed': False,
        })
        reservation._compute_lead_time()
        self.assertAlmostEqual(reservation.lead_time, 2.0)
        self.assertTrue(reservation.lead_time_computed)

    def test_compute_available_tables(self):
        """Test _compute_available_tables with and without existing overlapping reservations."""
        res1 = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '18:00',
            'ending_at': '20:00',
            'state': 'reserved',
        })
        self.assertIn(self.table2, res1.available_tables)

        # Compute for another reservation overlapping in time
        res2 = self.env['table.reservation'].new({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'date': self.tomorrow,
            'starting_at': '19:00',
            'ending_at': '21:00',
        })
        res2._compute_available_tables()
        available_ids = [t._origin.id if t._origin else t.id for t in res2.available_tables]
        self.assertNotIn(self.table1.id, available_ids)
        self.assertIn(self.table2.id, available_ids)

        # No floor set
        res_nofloor = self.env['table.reservation'].new({})
        res_nofloor._compute_available_tables()
        self.assertEqual(len(res_nofloor.available_tables), 0)

    def test_onchange_time_valid_and_invalid(self):
        """Test _onchange_time pattern validation."""
        reservation = self.env['table.reservation'].new({
            'starting_at': '14:30',
            'ending_at': '16:00',
        })
        reservation._onchange_time()

        # Invalid starting_at format
        reservation.starting_at = '25:00'
        with self.assertRaises(UserError):
            reservation._onchange_time()

        # Invalid ending_at format
        reservation.starting_at = '14:00'
        reservation.ending_at = '14:75'
        with self.assertRaises(UserError):
            reservation._onchange_time()

    def test_compute_booking_amount(self):
        """Test _compute_booking_amount with and without charge enabled."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id, self.table2.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '14:00',
        })
        param_obj = self.env['ir.config_parameter'].sudo()

        # When reservation charge is enabled
        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)
        reservation._compute_booking_amount()
        self.assertAlmostEqual(reservation.booking_amount, 75.0)

        # When reservation charge is disabled
        param_obj.set_bool('table_reservation_on_website.reservation_charge', False)
        reservation._compute_booking_amount()
        self.assertAlmostEqual(reservation.booking_amount, 0.0)

    def test_actions_workflow(self):
        """Test action_reserved, action_done, and action_cancel state transitions."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '13:00',
        })
        self.assertEqual(reservation.state, 'draft')

        reservation.action_reserved()
        self.assertEqual(reservation.state, 'reserved')

        reservation.action_done()
        self.assertEqual(reservation.state, 'done')

        reservation.action_cancel()
        self.assertEqual(reservation.state, 'cancel')

    def test_table_reservations_method(self):
        """Test table_reservations returns upcoming reserved records."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '15:00',
            'ending_at': '16:00',
            'state': 'reserved',
        })
        res_list = self.env['table.reservation'].table_reservations()
        res_ids = [r['id'] for r in res_list]
        self.assertIn(reservation.id, res_ids)

    def test_onchange_date_constraints(self):
        """Test _onchange_date constraints for past dates and invalid years."""
        # Past date constraint
        with self.assertRaises(ValidationError):
            self.env['table.reservation'].create({
                'customer_id': self.partner.id,
                'floor_id': self.floor.id,
                'booked_tables_ids': [(6, 0, [self.table1.id])],
                'date': self.today - timedelta(days=2),
                'starting_at': '12:00',
                'ending_at': '13:00',
                'state': 'draft',
            })

        # Year > 9999 constraint
        with self.assertRaises(ValidationError):
            res = self.env['table.reservation'].new({
                'customer_id': self.partner.id,
                'floor_id': self.floor.id,
                'booked_tables_ids': [(6, 0, [self.table1.id])],
                'date': self.tomorrow,
                'starting_at': '12:00',
                'ending_at': '13:00',
            })
            with patch.object(type(res), 'date', MagicMock(year=10000, __lt__=lambda s, o: False)):
                res._onchange_date()

    def test_check_lead_time_constraint(self):
        """Test _check_lead_time constraint."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '13:00',
            'lead_time': 2.0,
        })
        with self.assertRaises(ValidationError):
            reservation.write({'lead_time': 25.0})

        with self.assertRaises(ValidationError):
            reservation.write({'lead_time': -1.0})

    def test_check_table_overlap_constraint(self):
        """Test _check_table_overlap constraint prevents double bookings."""
        self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '10:00',
            'ending_at': '12:00',
            'state': 'reserved',
        })
        # Overlapping reservation on table1 should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['table.reservation'].create({
                'customer_id': self.partner.id,
                'floor_id': self.floor.id,
                'booked_tables_ids': [(6, 0, [self.table1.id])],
                'date': self.tomorrow,
                'starting_at': '11:00',
                'ending_at': '13:00',
                'state': 'reserved',
            })
        # Non-overlapping reservation on table1 should succeed
        non_overlap = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '13:00',
            'ending_at': '14:30',
            'state': 'reserved',
        })
        self.assertTrue(non_overlap)

    def test_edit_reservations(self):
        """Test edit_reservations from POS."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '13:00',
        })
        date_str = self.tomorrow.strftime('%Y-%m-%d')
        product_id = self.env['table.reservation'].edit_reservations(
            booking_id=reservation.id,
            date=date_str,
            customer=self.partner.id,
            start_time='14:00',
            end_time='16:00',
            floor=self.floor.id,
            table_ids=f"{self.table1.id},{self.table2.id}",
            lead="01:30",
            order_name='POS/TEST/001'
        )
        self.assertTrue(product_id)
        reservation.invalidate_recordset()
        self.assertEqual(reservation.starting_at, '14:00')
        self.assertEqual(reservation.ending_at, '16:00')
        self.assertAlmostEqual(reservation.lead_time, 1.5)
        self.assertEqual(reservation.order_name, 'POS/TEST/001')
        self.assertEqual(len(reservation.booked_tables_ids), 2)

        # Invalid year in edit
        with self.assertRaises(ValidationError):
            self.env['table.reservation'].edit_reservations(
                booking_id=reservation.id,
                date='10001-01-01',
                customer=self.partner.id,
                start_time='14:00',
                end_time='16:00',
                floor=self.floor.id,
                table_ids=[self.table1.id],
                lead=1.0,
            )

    def test_get_table_details(self):
        """Test get_table_details returns unreserved tables and handles constraints."""
        date_str = self.tomorrow.strftime('%Y-%m-%d')
        self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '14:00',
            'state': 'reserved',
        })
        tables = self.env['table.reservation'].get_table_details(
            floor_id=self.floor.id,
            date=date_str,
            start_time='12:30',
            end_time='13:30',
        )
        table_ids = [t['id'] for t in tables]
        self.assertNotIn(self.table1.id, table_ids)
        self.assertIn(self.table2.id, table_ids)

        # Test booked_table_id included in result
        tables_with_booked = self.env['table.reservation'].get_table_details(
            floor_id=self.floor.id,
            date=date_str,
            start_time='12:30',
            end_time='13:30',
            booked_table_id=[self.table1.id],
        )
        table_ids_with_booked = [t['id'] for t in tables_with_booked]
        self.assertIn(self.table1.id, table_ids_with_booked)

        # Invalid year check
        with self.assertRaises(ValidationError):
            self.env['table.reservation'].get_table_details(
                floor_id=self.floor.id,
                date='10000-01-01',
                start_time='12:00',
                end_time='13:00',
            )

    def test_get_reservation_amount(self):
        """Test get_reservation_amount calculation."""
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)

        amount = self.env['table.reservation'].get_reservation_amount(
            table_id=f"{self.table1.id},{self.table2.id}")
        self.assertAlmostEqual(amount, 75.0)

        param_obj.set_bool('table_reservation_on_website.reservation_charge', False)
        amount_disabled = self.env['table.reservation'].get_reservation_amount(
            table_id=f"{self.table1.id}")
        self.assertAlmostEqual(amount_disabled, 0.0)

        self.assertAlmostEqual(self.env['table.reservation'].get_reservation_amount(None), 0.0)

    def test_create_table_reservation_pos(self):
        """Test create_table_reservation from POS."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        date_str = self.tomorrow.strftime('%Y-%m-%d')
        product_id = self.env['table.reservation'].create_table_reservation(
            table_id=f"{self.table1.id}",
            date=date_str,
            start_time='17:00',
            end_time='19:00',
            partner=self.partner.id,
            lead_time='02:00',
            floor_id=self.floor.id,
            order_name='POS/TEST/002',
        )
        self.assertTrue(product_id)
        created = self.env['table.reservation'].search([
            ('order_name', '=', 'POS/TEST/002')
        ], limit=1)
        self.assertTrue(created)
        self.assertEqual(created.state, 'reserved')
        self.assertEqual(created.type, 'pos')
        self.assertAlmostEqual(created.lead_time, 2.0)

    def test_get_avail_table(self):
        """Test get_avail_table checking availability."""
        date_str = self.tomorrow.strftime('%Y-%m-%d')
        self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '14:00',
            'state': 'reserved',
        })
        is_avail = self.env['table.reservation'].get_avail_table(
            floor_id=self.floor.id,
            date=date_str,
            start_time='12:30',
            end_time='13:30',
            table_ids=f"{self.table1.id}",
        )
        self.assertFalse(is_avail)

        is_avail_table2 = self.env['table.reservation'].get_avail_table(
            floor_id=self.floor.id,
            date=date_str,
            start_time='12:30',
            end_time='13:30',
            table_ids=f"{self.table2.id}",
        )
        self.assertTrue(is_avail_table2)

        # Invalid year check
        with self.assertRaises(ValidationError):
            self.env['table.reservation'].get_avail_table(
                floor_id=self.floor.id,
                date='10005-01-01',
                start_time='12:00',
                end_time='13:00',
                table_ids=f"{self.table1.id}",
            )

    def test_cancel_reservations(self):
        """Test cancel_reservations method."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.partner.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table1.id])],
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '13:00',
            'state': 'reserved',
        })
        self.env['table.reservation'].cancel_reservations(reservation.id)
        reservation.invalidate_recordset()
        self.assertEqual(reservation.state, 'cancel')

    def test_add_payment(self):
        """Test add_payment method."""
        res = self.env['table.reservation'].add_payment(self.table1.id, self.floor.id)
        self.assertIn('product', res)
        self.assertAlmostEqual(res['rate'], 25.0)

