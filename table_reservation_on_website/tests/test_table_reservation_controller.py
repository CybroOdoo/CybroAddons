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
"""Test suite for table_reservation_on_website controller."""
from datetime import date, datetime, timedelta
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.table_reservation_on_website.controllers.table_reservation_on_website import TableReservation


@tagged('post_install', '-at_install')
class TestTableReservationController(TransactionCase):
    """Test all routes and methods of TableReservation controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = TableReservation()
        cls.floor = cls.env['restaurant.floor'].create({'name': 'Controller Floor'})
        cls.table = cls.env['restaurant.table'].create({
            'table_number': 5,
            'floor_id': cls.floor.id,
            'rate': 30.0,
            'seats': 4,
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Controller Test POS',
            'module_pos_restaurant': True,
            'set_opening_hours': True,
            'opening_hour': 10.0,
            'closing_hour': 23.0,
        })
        cls.tomorrow = date.today() + timedelta(days=1)
        cls.tomorrow_str = cls.tomorrow.strftime('%Y-%m-%d')

    def test_float_to_time(self):
        """Test float_to_time conversion method."""
        self.assertEqual(self.controller.float_to_time(8.5), '08:30')
        self.assertEqual(self.controller.float_to_time(10.0), '10:00')

    def test_table_reservation_route(self):
        """Test table_reservation route rendering."""
        with MockRequest(self.env):
            with patch('odoo.http.request.render', return_value='rendered_html') as mock_render:
                res = self.controller.table_reservation()
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'rendered_html')
                mock_render.assert_called_once()
                args, kwargs = mock_render.call_args
                self.assertEqual(args[0], 'table_reservation_on_website.table_reservation')
                self.assertEqual(args[1]['opening_hour'], '10:00')
                self.assertEqual(args[1]['closing_hour'], '23:00')

    def test_restaurant_floors(self):
        """Test restaurant_floors route."""
        with MockRequest(self.env):
            with patch('odoo.http.request.render', return_value='rendered_floors') as mock_render:
                res = self.controller.restaurant_floors(
                    date=self.tomorrow_str,
                    start_time='12:00',
                    end_time='14:00'
                )
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'rendered_floors')
                mock_render.assert_called_once()

    def test_restaurant_floors_lead_time_failure(self):
        """Test restaurant_floors when lead time check fails."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.reservation_lead_time', 5.0)

        today_str = date.today().strftime('%Y-%m-%d')
        now_time = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')

        with MockRequest(self.env):
            with self.assertRaises(ValidationError):
                self.controller.restaurant_floors(
                    date=today_str,
                    start_time=now_time,
                    end_time='23:00',
                )

    def test_restaurant_floors_tables(self):
        """Test restaurant_floors_tables JSON-RPC endpoint."""
        with MockRequest(self.env):
            data = self.controller.restaurant_floors_tables(
                floors_id=str(self.floor.id),
                date=self.tomorrow_str,
                start='12:00',
                end='14:00',
            )
            self.assertIn(self.table.id, data)
            self.assertEqual(data[self.table.id]['name'], 5)

        # Missing or 0 floor_id
        with MockRequest(self.env):
            empty_data = self.controller.restaurant_floors_tables(floors_id='0')
            self.assertEqual(empty_data, {})

        # Invalid year > 9999
        with MockRequest(self.env):
            invalid_data = self.controller.restaurant_floors_tables(
                floors_id=str(self.floor.id),
                date='10001-01-01',
            )
            self.assertEqual(invalid_data, {})

    def test_booking_confirm_no_tables(self):
        """Test booking_confirm without tables raises ValidationError."""
        with MockRequest(self.env):
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm()

    def test_booking_confirm_payment_disabled(self):
        """Test booking_confirm when reservation_charge is False."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', False)

        with MockRequest(self.env):
            with patch('odoo.http.request.render', return_value='confirmed_page') as mock_render:
                res = self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='18:00',
                    end_time='20:00',
                )
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'confirmed_page')
                mock_render.assert_called_with('table_reservation_on_website.table_reserved_template')

        created = self.env['table.reservation'].search([
            ('floor_id', '=', self.floor.id),
            ('date', '=', self.tomorrow),
            ('starting_at', '=', '18:00'),
        ], limit=1)
        self.assertTrue(created)
        self.assertEqual(created.state, 'reserved')
        self.assertEqual(created.type, 'website')

    def test_booking_confirm_payment_enabled(self):
        """Test booking_confirm when reservation_charge is True."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', True)

        booking_product = self.env.ref(
            'table_reservation_on_website.product_product_table_booking')
        orig_list_price = booking_product.list_price

        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.user.partner_id.id,
        })

        with MockRequest(self.env):
            with patch.object(type(self.env['website']), '_create_cart', return_value=sale_order), \
                 patch('odoo.http.request.redirect', return_value='redirect_cart') as mock_redir:
                res = self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='18:00',
                    end_time='20:00',
                )
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'redirect_cart')
                mock_redir.assert_called_with('/shop/cart')
                self.assertEqual(sale_order.floors, int(self.floor.id))
                self.assertAlmostEqual(sale_order.booking_amount, 30.0)
                # Ensure shared product list_price is NOT overwritten
                self.assertEqual(booking_product.list_price, orig_list_price)

    def test_booking_confirm_route_auth_and_csrf(self):
        """Test booking_confirm route requires user auth and enforces CSRF and POST."""
        routing = getattr(self.controller.booking_confirm, 'original_routing', {})
        self.assertEqual(routing.get('auth'), 'user')
        self.assertFalse(routing.get('csrf') is False)
        self.assertIn('POST', routing.get('methods', []))

    def test_booking_confirm_public_user_blocked(self):
        """Test booking_confirm blocks unauthenticated/public users."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', False)
        public_user = self.env.ref('base.public_user')
        with MockRequest(self.env(user=public_user)):
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='18:00',
                    end_time='20:00',
                )

    def test_booking_confirm_availability_recheck(self):
        """Test availability is re-checked on confirm and blocks overlapping reservations."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', False)

        # Create existing reservation for self.table tomorrow from 14:00 to 16:00
        self.env['table.reservation'].create({
            'customer_id': self.env.user.partner_id.id,
            'booked_tables_ids': [(6, 0, [self.table.id])],
            'floor_id': self.floor.id,
            'date': self.tomorrow,
            'starting_at': '14:00',
            'ending_at': '16:00',
            'state': 'reserved',
        })

        with MockRequest(self.env):
            # Overlapping slot (15:00 - 17:00) must raise ValidationError
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='15:00',
                    end_time='17:00',
                )

            # Non-overlapping slot (16:00 - 18:00) must succeed
            with patch('odoo.http.request.render', return_value='confirmed_page'):
                res = self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='16:00',
                    end_time='18:00',
                )
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'confirmed_page')

    def test_table_reservation_pos(self):
        """Test table_reservation_pos creation."""
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)

        with MockRequest(self.env):
            self.controller.table_reservation_pos(table_id=self.table.id)
            res = self.env['table.reservation'].search([
                ('floor_id', '=', self.floor.id),
                ('type', '=', 'pos'),
            ], limit=1)
            self.assertTrue(res)
            self.assertAlmostEqual(res.booking_amount, 30.0)

        table2 = self.env['restaurant.table'].create({
            'table_number': 6,
            'floor_id': self.floor.id,
            'rate': 30.0,
            'seats': 4,
        })
        param_obj.set_bool('table_reservation_on_website.reservation_charge', False)
        with MockRequest(self.env):
            self.controller.table_reservation_pos(table_id=table2.id)
            res2 = self.env['table.reservation'].search([
                ('floor_id', '=', self.floor.id),
                ('type', '=', 'pos'),
                ('booked_tables_ids', 'in', [table2.id]),
            ], limit=1)
            self.assertTrue(res2)
            self.assertEqual(res2.booking_amount, 0.0)

    def test_active_floor_tables(self):
        """Test active_floor_tables returns booked table IDs in current window."""
        reservation = self.env['table.reservation'].create({
            'customer_id': self.env.user.partner_id.id,
            'floor_id': self.floor.id,
            'booked_tables_ids': [(6, 0, [self.table.id])],
            'date': date.today(),
            'starting_at': '00:00',
            'ending_at': '23:59',
            'state': 'reserved',
            'lead_time': 0.0,
        })

        with MockRequest(self.env):
            active_tables = self.controller.active_floor_tables(floor_id=self.floor.id)
            self.assertIsInstance(active_tables, list)
            self.assertIn(self.table.id, active_tables)

    def test_table_reservation_route_no_opening_hours(self):
        """Test table_reservation route when opening hours are not configured."""
        self.pos_config.write({'set_opening_hours': False})
        with MockRequest(self.env):
            with patch('odoo.http.request.render', return_value='rendered_html') as mock_render:
                res = self.controller.table_reservation()
                result_data = res.get_data(as_text=True) if hasattr(res, 'get_data') else res
                self.assertEqual(result_data, 'rendered_html')
                args, _kwargs = mock_render.call_args
                self.assertEqual(args[1]['opening_hour'], '00:00')
                self.assertEqual(args[1]['closing_hour'], '24:00')

            with patch.object(self.controller, 'float_to_time', side_effect=ValueError), \
                 patch('odoo.http.request.render', return_value='rendered_html') as mock_render:
                self.controller.table_reservation()
                args, _kwargs = mock_render.call_args
                self.assertEqual(args[1]['opening_hour'], '00:00')
                self.assertEqual(args[1]['closing_hour'], '23:59')

    def test_restaurant_floors_tables_booked_filter(self):
        """Test restaurant_floors_tables filters out already booked tables."""
        self.env['table.reservation'].create({
            'customer_id': self.env.user.partner_id.id,
            'booked_tables_ids': [(6, 0, [self.table.id])],
            'floor_id': self.floor.id,
            'date': self.tomorrow,
            'starting_at': '12:00',
            'ending_at': '14:00',
            'state': 'reserved',
        })
        with MockRequest(self.env):
            data = self.controller.restaurant_floors_tables(
                floors_id=str(self.floor.id),
                date=self.tomorrow_str,
                start='12:30',
                end='13:30',
            )
            self.assertNotIn(self.table.id, data)

    def test_restaurant_floors_tables_lead_time_failure(self):
        """Test restaurant_floors_tables returns empty dict when lead time check fails."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.reservation_lead_time', 5.0)

        today_str = date.today().strftime('%Y-%m-%d')
        now_time = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')

        with MockRequest(self.env):
            data = self.controller.restaurant_floors_tables(
                floors_id=str(self.floor.id),
                date=today_str,
                start=now_time,
                end='23:00',
            )
            self.assertEqual(data, {})

    def test_restaurant_floors_tables_with_payment(self):
        """Test restaurant_floors_tables returns rate when reservation_charge is True."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', True)
        with MockRequest(self.env):
            data = self.controller.restaurant_floors_tables(
                floors_id=str(self.floor.id),
                date=self.tomorrow_str,
                start='12:00',
                end='14:00',
            )
            self.assertIn(self.table.id, data)
            self.assertEqual(data[self.table.id]['rate'], 30.0)

    def test_booking_confirm_invalid_dates_and_times(self):
        """Test booking_confirm validation for invalid dates and times."""
        with MockRequest(self.env):
            # Past date
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date='2020-01-01',
                    start_time='18:00',
                    end_time='20:00',
                )

            # Invalid date format
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date='invalid-date',
                    start_time='18:00',
                    end_time='20:00',
                )

            # End time before start time
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='18:00',
                    end_time='17:00',
                )

    def test_booking_confirm_lead_time_failure(self):
        """Test booking_confirm raises ValidationError when lead time is not met."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.reservation_lead_time', 4.0)

        today_str = date.today().strftime('%Y-%m-%d')
        now_time = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')

        with MockRequest(self.env):
            with self.assertRaises(ValidationError):
                self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=today_str,
                    start_time=now_time,
                    end_time='23:00',
                )

    def test_booking_confirm_payment_non_draft_cart(self):
        """Test booking_confirm resets non-draft cart before creating new cart."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.reservation_charge', True)

        draft_cart = self.env['sale.order'].create({
            'partner_id': self.env.user.partner_id.id,
            'state': 'draft',
        })
        sale_order_done = self.env['sale.order'].create({
            'partner_id': self.env.user.partner_id.id,
            'state': 'sale',
        })

        with MockRequest(self.env):
            with patch('odoo.http.request.cart', new=sale_order_done, create=True), \
                 patch.object(type(self.env['website']), 'sale_reset') as mock_reset, \
                 patch.object(type(self.env['website']), '_create_cart', return_value=draft_cart), \
                 patch('odoo.http.request.redirect', return_value='redirect_cart'):
                res = self.controller.booking_confirm(
                    tables=str(self.table.id),
                    floors=str(self.floor.id),
                    date=self.tomorrow_str,
                    start_time='18:00',
                    end_time='20:00',
                )
                mock_reset.assert_called_once()
                self.assertEqual(draft_cart.floors, int(self.floor.id))
                self.assertAlmostEqual(draft_cart.booking_amount, 30.0)
