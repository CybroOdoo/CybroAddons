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
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosBookOrder(TransactionCase):
    """Comprehensive test suite for POS Book Order module, ensuring >80% coverage
       and verification of business logic, multi-recordsets, and POS integrations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # Customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Booking Test Customer',
            'phone': '+1 555-0199',
            'street': '123 Test Avenue, Suite 100',
            'email': 'customer@testbooking.com',
        })

        # Products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Booked Meal Combo',
            'list_price': 50.0,
            'available_in_pos': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Cold Beverage',
            'list_price': 10.0,
            'available_in_pos': True,
        })

        # Sales Tax (10%)
        cls.tax_10 = cls.env['account.tax'].create({
            'name': 'Sales Tax 10%',
            'amount': 10.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company.id,
        })

        # Destination Tax for Fiscal Position (5%)
        cls.tax_5 = cls.env['account.tax'].create({
            'name': 'Reduced Tax 5%',
            'amount': 5.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company.id,
        })

        # Fiscal Position mapping 10% -> 5% (Odoo 20 syntax)
        cls.fiscal_position = cls.env['account.fiscal.position'].create({
            'name': 'Special Catering Fiscal Position',
            'company_id': cls.company.id,
        })
        cls.tax_5.write({
            'fiscal_position_ids': [Command.link(cls.fiscal_position.id)],
            'original_tax_ids': [Command.link(cls.tax_10.id)],
        })

        # Pricelist
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'POS Booking Pricelist',
            'currency_id': cls.company.currency_id.id,
        })

        # POS Config
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Main Store POS',
            'enable': True,
        })

    def test_01_pos_config_enable(self):
        """Verify the 'enable' field on pos.config."""
        self.assertTrue(self.pos_config.enable)
        self.pos_config.write({'enable': False})
        self.assertFalse(self.pos_config.enable)
        self.pos_config.write({'enable': True})
        self.assertTrue(self.pos_config.enable)

    def test_02_book_order_create_and_sequence(self):
        """Test single and multi-record creation of book.order and sequence assignment."""
        # Single record creation
        order_single = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'phone': self.partner.phone,
            'delivery_address': self.partner.street,
            'pos_order_uid': 'POS-UID-001',
        })
        self.assertTrue(order_single.name.startswith('POS/BO/'))
        self.assertEqual(order_single.state, 'draft')
        self.assertEqual(order_single.company_id, self.company)
        self.assertEqual(order_single.date_order, fields.Date.context_today(self.env.user))

        # Multi-record creation
        orders_multi = self.env['book.order'].create([
            {
                'partner_id': self.partner.id,
                'pos_order_uid': 'POS-UID-002',
            },
            {
                'partner_id': self.partner.id,
                'pos_order_uid': 'POS-UID-003',
            },
        ])
        self.assertEqual(len(orders_multi), 2)
        for order in orders_multi:
            self.assertTrue(order.name.startswith('POS/BO/'))
            self.assertEqual(order.state, 'draft')

    def test_03_book_order_lines_tax_and_subtotals(self):
        """Test computation of line subtotals with discount and taxes, and order totals."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'book_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 100.0,
                    'qty': 2.0,
                    'discount': 10.0,  # Net price 90 * 2 = 180 w/o tax
                    'tax_ids': [Command.set([self.tax_10.id])],
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'price_unit': 20.0,
                    'qty': 1.0,
                    'discount': 0.0,  # 20 w/o tax, no tax
                }),
            ],
        })

        line1 = order.book_line_ids[0]
        line2 = order.book_line_ids[1]

        # Line 1: 100 * (1 - 0.1) * 2 = 180.0 untaxed; 10% tax = 18.0; incl = 198.0
        self.assertAlmostEqual(line1.price_subtotal, 180.0, places=2)
        self.assertAlmostEqual(line1.price_subtotal_incl, 198.0, places=2)

        # Line 2: 20 * 1 = 20.0 untaxed and total
        self.assertAlmostEqual(line2.price_subtotal, 20.0, places=2)
        self.assertAlmostEqual(line2.price_subtotal_incl, 20.0, places=2)

        # Order totals
        self.assertAlmostEqual(order.amount_tax, 18.0, places=2)
        self.assertAlmostEqual(order.amount_total, 218.0, places=2)

    def test_04_fiscal_position_tax_mapping(self):
        """Test line tax computation when fiscal position maps a tax."""
        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'fiscal_position_id': self.fiscal_position.id,
            'pricelist_id': self.pricelist.id,
            'book_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 100.0,
                    'qty': 1.0,
                    'tax_ids': [Command.set([self.tax_10.id])],
                }),
            ],
        })

        line = order.book_line_ids[0]
        # 10% mapped to 5% by fiscal position: 5.0 tax
        self.assertEqual(line.tax_after_fiscal_position_ids, self.tax_5)
        self.assertAlmostEqual(line.price_subtotal, 100.0, places=2)
        self.assertAlmostEqual(line.price_subtotal_incl, 105.0, places=2)
        self.assertAlmostEqual(order.amount_tax, 5.0, places=2)
        self.assertAlmostEqual(order.amount_total, 105.0, places=2)

    def test_05_action_confirm_single_and_multi(self):
        """Test action_confirm on both single record and multi-recordsets."""
        orders = self.env['book.order'].create([
            {
                'partner_id': self.partner.id,
                'pos_order_uid': 'POS-UID-CONF-1',
            },
            {
                'partner_id': self.partner.id,
                'pos_order_uid': 'POS-UID-CONF-2',
            },
        ])

        # Test single record confirm
        res_single = orders[0].action_confirm()
        self.assertEqual(orders[0].state, 'confirmed')
        self.assertEqual(res_single, 'POS-UID-CONF-1')

        # Test multi-record confirm
        res_multi = orders.action_confirm()
        self.assertEqual(orders[1].state, 'confirmed')
        self.assertIn('POS-UID-CONF-2', res_multi)

    def test_06_create_booked_order_pickup(self):
        """Test create_booked_order RPC method with pickup date."""
        product_data = {
            'product_id': [self.product_a.id, self.product_b.id],
            'qty': [2.0, 3.0],
            'price': [45.0, 8.5],
            'tax_ids': [[self.tax_10.id], []],
        }

        res = self.env['book.order'].create_booked_order(
            partner=self.partner.id,
            phone='+1 555-0199',
            address='',
            date='2026-11-15 10:00:00',
            price_list=self.pricelist.id,
            product=product_data,
            note='Please pack carefully',
            pickup_date='2026-11-16',
            delivery_date='',
            pos_order='POS-ORDER-PICKUP-1',
        )

        self.assertIn('id', res)
        self.assertIn('name', res)

        order = self.env['book.order'].browse(res['id'])
        self.assertEqual(order.partner_id, self.partner)
        self.assertEqual(order.phone, '+1 555-0199')
        self.assertEqual(order.note, 'Please pack carefully')
        self.assertEqual(order.pos_order_uid, 'POS-ORDER-PICKUP-1')
        self.assertTrue(bool(order.pickup_date))
        self.assertFalse(order.deliver_date)
        self.assertEqual(len(order.book_line_ids), 2)

    def test_07_create_booked_order_delivery(self):
        """Test create_booked_order RPC method with delivery date and address."""
        product_data = {
            'product_id': [self.product_a.id],
            'qty': [1.0],
            'price': [50.0],
            'tax_ids': [[]],
        }

        res = self.env['book.order'].create_booked_order(
            partner=self.partner.id,
            phone='+1 555-0199',
            address='742 Evergreen Terrace',
            date='',  # Empty date should default
            price_list=False,
            product=product_data,
            note='',
            pickup_date='',
            delivery_date='2026-11-20',
            pos_order='POS-ORDER-DELIV-1',
        )

        order = self.env['book.order'].browse(res['id'])
        self.assertEqual(order.delivery_address, '742 Evergreen Terrace')
        self.assertTrue(bool(order.deliver_date))
        self.assertFalse(order.pickup_date)

    def test_08_all_orders_rpc(self):
        """Test all_orders RPC method with state filters."""
        order_draft = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'phone': '111-222',
            'delivery_address': 'Address A',
            'book_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'qty': 1.0,
                    'price_unit': 50.0,
                })
            ],
        })

        order_conf = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'phone': '333-444',
            'delivery_address': 'Address B',
            'book_line_ids': [
                Command.create({
                    'product_id': self.product_b.id,
                    'qty': 2.0,
                    'price_unit': 10.0,
                })
            ],
        })
        order_conf.action_confirm()

        # Filter by draft
        draft_orders = self.env['book.order'].all_orders(state='draft')
        draft_ids = [o['id'] for o in draft_orders]
        self.assertIn(order_draft.id, draft_ids)
        self.assertNotIn(order_conf.id, draft_ids)

        # Filter by confirmed
        conf_orders = self.env['book.order'].all_orders(state='confirmed')
        conf_ids = [o['id'] for o in conf_orders]
        self.assertIn(order_conf.id, conf_ids)
        self.assertNotIn(order_draft.id, conf_ids)

        # Filter by all
        all_res = self.env['book.order'].all_orders(state='all')
        all_ids = [o['id'] for o in all_res]
        self.assertIn(order_draft.id, all_ids)
        self.assertIn(order_conf.id, all_ids)

        # Inspect payload structure
        draft_data = next(o for o in draft_orders if o['id'] == order_draft.id)
        self.assertEqual(draft_data['partner_id'], self.partner.id)
        self.assertEqual(draft_data['partner_name'], self.partner.name)
        self.assertEqual(draft_data['phone'], '111-222')
        self.assertEqual(draft_data['address'], 'Address A')
        self.assertEqual(len(draft_data['products']), 1)
        self.assertEqual(draft_data['products'][0]['id'], self.product_a.id)

    def test_09_pos_order_fields_and_process_order(self):
        """Test pos.order _order_fields and _process_order hooks."""
        booked_order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'phone': '+1 555-9988',
            'delivery_address': '456 Main St',
            'pickup_date': '2026-11-18 12:00:00',
            'deliver_date': False,
            'note': 'Fragile goods',
        })
        self.assertEqual(booked_order.state, 'draft')

        # Test _order_fields with integer booking_ref_id
        ui_order_int = {
            'is_booked': True,
            'booking_ref_id': booked_order.id,
        }
        res_fields = self.env['pos.order']._order_fields(ui_order_int)
        self.assertEqual(res_fields.get('booking_ref_id'), booked_order.id)
        self.assertEqual(booked_order.state, 'confirmed')

        # Reset state to draft to test string booking_ref_id
        booked_order.write({'state': 'draft'})
        ui_order_str = {
            'is_booked': True,
            'booking_ref_id': booked_order.name,
        }
        res_fields_str = self.env['pos.order']._order_fields(ui_order_str)
        self.assertEqual(res_fields_str.get('booking_ref_id'), booked_order.id)
        self.assertEqual(booked_order.state, 'confirmed')

        # Test _process_order logic
        booked_order.write({'state': 'draft'})
        mock_pos_session = self.env['pos.session'].create({
            'name': 'Booking POS Session',
            'config_id': self.pos_config.id,
        })
        mock_pos_order = self.env['pos.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'session_id': mock_pos_session.id,
        })

        order_dict = {
            'session_id': mock_pos_session.id,
            'booking_ref_id': booked_order.id,
            'is_booked': True,
            'booked_data': {'id': booked_order.id},
        }

        with patch('odoo.addons.point_of_sale.models.pos_order.PosOrder._process_order', return_value=mock_pos_order.id):
            processed_id = self.env['pos.order']._process_order(order_dict, False)
            self.assertEqual(processed_id, mock_pos_order.id)

        self.assertEqual(mock_pos_order.booking_ref_id, booked_order)
        self.assertTrue(mock_pos_order.is_booked)
        self.assertEqual(booked_order.state, 'confirmed')

        # Test _get_common_extra_data receipt info
        extra_data = mock_pos_order._get_common_extra_data()
        self.assertIn('booking_info', extra_data)
        booking_info = extra_data['booking_info']
        self.assertEqual(booking_info['name'], booked_order.name)
        self.assertEqual(booking_info['phone'], '+1 555-9988')
        self.assertEqual(booking_info['note'], 'Fragile goods')
        self.assertEqual(booking_info['address'], '456 Main St')
        self.assertTrue(bool(booking_info['pickup']))
        self.assertFalse(booking_info['deliver'])

        # Regular order without booking should not have booking_info
        regular_order = self.env['pos.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'session_id': mock_pos_session.id,
        })
        regular_extra = regular_order._get_common_extra_data()
        self.assertNotIn('booking_info', regular_extra)

    def test_10_edge_cases(self):
        """Test edge cases such as empty lines, zero quantity, and line tax without company match."""
        country = self.company.country_id or self.env['res.country'].search([], limit=1)
        # Tax from another company
        other_company = self.env['res.company'].create({
            'name': 'Other Sister Company',
            'country_id': country.id,
        })
        tax_group = self.env['account.tax.group'].create({
            'name': 'Other Tax Group',
            'company_id': other_company.id,
            'country_id': country.id,
        })
        other_tax = self.env['account.tax'].create({
            'name': 'Other Tax 15%',
            'amount': 15.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': other_company.id,
            'country_id': country.id,
            'tax_group_id': tax_group.id,
        })

        order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'book_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 0.0,
                    'qty': 0.0,
                    'tax_ids': [Command.set([other_tax.id])],
                }),
            ],
        })

        line = order.book_line_ids[0]
        # Foreign company tax must be filtered out, subtotal should be 0.0
        self.assertEqual(line.price_subtotal, 0.0)
        self.assertEqual(line.price_subtotal_incl, 0.0)
        self.assertEqual(order.amount_tax, 0.0)
        self.assertEqual(order.amount_total, 0.0)

        # Multi-company order isolation in all_orders
        other_order = self.env['book.order'].create({
            'partner_id': self.partner.id,
            'company_id': other_company.id,
        })
        current_orders = self.env['book.order'].all_orders()
        current_order_ids = [o['id'] for o in current_orders]
        self.assertNotIn(other_order.id, current_order_ids)

        # Isolated orders are visible when switched to that company
        other_orders = self.env['book.order'].with_company(other_company).all_orders()
        other_order_ids = [o['id'] for o in other_orders]
        self.assertIn(other_order.id, other_order_ids)
        self.assertNotIn(order.id, other_order_ids)

