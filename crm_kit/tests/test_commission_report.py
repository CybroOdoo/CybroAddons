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
"""Unit tests for the commission.report wizard model."""

import io
import json
from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase, new_test_user


class MockResponse:
    """Mock response object with a binary stream."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestCommissionReport(TransactionCase):
    """Test cases for commission.report model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cancel any pre-existing sale orders so test calculations have a clean slate
        cls.env['sale.order'].search([('state', '!=', 'cancel')]).write({'state': 'cancel'})

        group_salesman = 'sales_team.group_sale_salesman'
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Product A',
            'categ_id': cls.category.id,
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Product B',
            'categ_id': cls.category.id,
            'list_price': 50.0,
            'taxes_id': [Command.clear()],
        })

        # Salesperson Alice with Product Commission Plan
        cls.comm_product = cls.env['crm.commission'].create({
            'name': 'Product Plan Alice',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'product',
            'product_comm_ids': [(0, 0, {
                'product_id': cls.product_a.id,
                'category_id': cls.category.id,
                'percentage': 10.0,
                'amount': 50.0,  # Max cap 50.0
            })],
        })
        cls.user_alice = new_test_user(cls.env, login='rep_alice', groups=group_salesman)
        cls.user_alice.commission_id = cls.comm_product.id

        # Salesperson Bob with Straight Revenue Commission Plan
        cls.comm_straight = cls.env['crm.commission'].create({
            'name': 'Straight Revenue Plan Bob',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'revenue',
            'revenue_type': 'straight',
            'straight_commission_rate': 15.0,
        })
        cls.user_bob = new_test_user(cls.env, login='rep_bob', groups=group_salesman)
        cls.user_bob.commission_id = cls.comm_straight.id

        # Salesperson Carol with Graduated Revenue Commission Plan
        cls.comm_graduated = cls.env['crm.commission'].create({
            'name': 'Graduated Revenue Plan Carol',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'revenue',
            'revenue_type': 'graduated',
            'revenue_grd_comm_ids': [
                (0, 0, {
                    'amount_from': 0.0,
                    'amount_to': 1000.0,
                    'graduated_commission_rate': 5.0,
                }),
                (0, 0, {
                    'amount_from': 1000.0,
                    'amount_to': 5000.0,
                    'graduated_commission_rate': 10.0,
                }),
            ],
        })
        cls.user_carol = new_test_user(cls.env, login='rep_carol', groups=group_salesman)
        cls.user_carol.commission_id = cls.comm_graduated.id

        # Sales Team with Dave (team has commission plan fallback)
        cls.comm_team = cls.env['crm.commission'].create({
            'name': 'Team Straight Plan',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'revenue',
            'revenue_type': 'straight',
            'straight_commission_rate': 8.0,
        })
        cls.user_dave = new_test_user(cls.env, login='rep_dave', groups=group_salesman)
        cls.sales_team = cls.env['crm.team'].create({
            'name': 'Commission Alpha Team',
            'member_ids': [Command.set([cls.user_dave.id])],
            'commission_id': cls.comm_team.id,
        })

    def _create_confirmed_order(self, user, product, qty, price_unit, date_order='2026-06-15'):
        """Helper to create and confirm a sale order."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': user.id,
            'date_order': date_order,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': price_unit,
                'tax_ids': [Command.clear()],
            })],
        })
        order.action_confirm()
        return order

    def test__check_date_validation(self):
        """Test _check_date_validation ensures date_to is not earlier than date_from."""
        # Valid date range
        wizard = self.env['commission.report'].create({
            'date_from': '2026-01-01',
            'date_to': '2026-06-30',
        })
        wizard._check_date_validation()

        # Same start and end date is valid
        wizard.write({'date_to': '2026-01-01'})
        wizard._check_date_validation()

        # Inverted date range raises ValidationError on create
        with self.assertRaises(ValidationError):
            self.env['commission.report'].create({
                'date_from': '2026-12-31',
                'date_to': '2026-01-01',
            })

        # Inverted date range raises ValidationError on write
        with self.assertRaises(ValidationError):
            wizard.write({'date_from': '2026-12-31', 'date_to': '2026-01-01'})

    def test_onchange_salesperson_ids(self):
        """Test onchange_salesperson_ids toggles is_sales_person flag properly."""
        wizard = self.env['commission.report'].create({})
        self.assertFalse(wizard.is_sales_person)

        wizard.salesperson_ids = [Command.set(self.user_alice.ids)]
        wizard.onchange_salesperson_ids()
        self.assertTrue(wizard.is_sales_person)

        wizard.salesperson_ids = [Command.clear()]
        wizard.onchange_salesperson_ids()
        self.assertFalse(wizard.is_sales_person)

    def test_onchange_sales_team_ids(self):
        """Test onchange_sales_team_ids toggles is_sales_team flag properly."""
        wizard = self.env['commission.report'].create({})
        self.assertFalse(wizard.is_sales_team)

        wizard.sales_team_ids = [Command.set(self.sales_team.ids)]
        wizard.onchange_sales_team_ids()
        self.assertTrue(wizard.is_sales_team)

        wizard.sales_team_ids = [Command.clear()]
        wizard.onchange_sales_team_ids()
        self.assertFalse(wizard.is_sales_team)

    def test_sales_team_constrains(self):
        """Test sales_team_constrains validation for team and salesperson setup."""
        # Case 1: Team without members raises ValidationError on create
        empty_team = self.env['crm.team'].create({'name': 'Empty Test Team'})
        with self.assertRaises(ValidationError) as cm:
            self.env['commission.report'].create({
                'sales_team_ids': [Command.set(empty_team.ids)],
            })
        self.assertIn("haven't any Salespersons", str(cm.exception))

        # Case 2: Team with members but no commission plan raises ValidationError on create
        user_no_comm = new_test_user(
            self.env, login='rep_no_comm', groups='sales_team.group_sale_salesman'
        )
        team_no_plan = self.env['crm.team'].create({
            'name': 'No Plan Team',
            'member_ids': [Command.set(user_no_comm.ids)],
            'commission_id': False,
        })
        with self.assertRaises(ValidationError) as cm:
            self.env['commission.report'].create({
                'sales_team_ids': [Command.set(team_no_plan.ids)],
            })
        self.assertIn("haven't any Commission Plan", str(cm.exception))

        # Case 3: Salesperson without commission plan raises ValidationError on create
        with self.assertRaises(ValidationError) as cm:
            self.env['commission.report'].create({
                'salesperson_ids': [Command.set(user_no_comm.ids)],
            })
        self.assertIn("haven't any Commission Plan", str(cm.exception))

        # Case 4: Valid salesperson passes without error
        wizard_sp_valid = self.env['commission.report'].create({
            'salesperson_ids': [Command.set(self.user_alice.ids)],
        })
        wizard_sp_valid.sales_team_constrains()

        # Case 5: Valid sales team passes without error
        wizard_team_valid = self.env['commission.report'].create({
            'sales_team_ids': [Command.set(self.sales_team.ids)],
        })
        wizard_team_valid.sales_team_constrains()

    def test_action_print_xls_report(self):
        """Test action_print_xls_report computes correct figures and returns report action."""
        # 1. Alice (Product commission: 10%, max cap 50.0)
        # Order 1: 2 * 100 = 200 -> 10% = 20.0 (below 50.0 cap)
        self._create_confirmed_order(self.user_alice, self.product_a, 2, 100.0)
        wizard_alice = self.env['commission.report'].create({
            'salesperson_ids': [Command.set(self.user_alice.ids)],
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
        })
        res_alice = wizard_alice.action_print_xls_report()
        self.assertEqual(res_alice['type'], 'ir.actions.report')
        self.assertEqual(res_alice['report_type'], 'xlsx')
        data_alice = json.loads(res_alice['data']['options'])
        self.assertIn(self.user_alice.name, data_alice['user_commission_salesperson'])
        self.assertIn(20.0, data_alice['commission_list'])
        self.assertIn(200.0, data_alice['total_list'])

        # 2. Bob (Straight revenue commission: 15%)
        # Order: 4 * 100 = 400 -> 15% = 60.0
        self._create_confirmed_order(self.user_bob, self.product_a, 4, 100.0)
        wizard_bob = self.env['commission.report'].create({
            'salesperson_ids': [Command.set(self.user_bob.ids)],
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
        })
        res_bob = wizard_bob.action_print_xls_report()
        data_bob = json.loads(res_bob['data']['options'])
        self.assertIn(self.user_bob.name, data_bob['user_commission_salesperson'])
        self.assertIn(60.0, data_bob['commission_list'])
        self.assertIn(400.0, data_bob['total_list'])

        # 3. Carol (Graduated revenue commission: 0-1000 @ 5%, 1000-5000 @ 10%)
        # Order: 20 * 100 = 2000 -> 10% = 200.0
        self._create_confirmed_order(self.user_carol, self.product_a, 20, 100.0)
        wizard_carol = self.env['commission.report'].create({
            'salesperson_ids': [Command.set(self.user_carol.ids)],
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
        })
        res_carol = wizard_carol.action_print_xls_report()
        data_carol = json.loads(res_carol['data']['options'])
        self.assertIn(self.user_carol.name, data_carol['user_commission_salesperson'])
        self.assertIn(200.0, data_carol['commission_list'])
        self.assertIn(2000.0, data_carol['total_list'])

        # 4. Sales Team (Dave with team plan fallback: 8%)
        # Order: 5 * 100 = 500 -> 8% = 40.0
        self._create_confirmed_order(self.user_dave, self.product_a, 5, 100.0)
        wizard_team = self.env['commission.report'].create({
            'sales_team_ids': [Command.set(self.sales_team.ids)],
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
        })
        res_team = wizard_team.action_print_xls_report()
        data_team = json.loads(res_team['data']['options'])
        self.assertIn(self.sales_team.name, data_team['commission_sales_team'])
        self.assertIn(self.user_dave.name, data_team['commission_salesperson'])
        self.assertIn(40.0, data_team['commission'])
        self.assertIn(500.0, data_team['commission_total'])

        # 5. Default with neither salesperson nor team selected
        wizard_default = self.env['commission.report'].create({})
        res_default = wizard_default.action_print_xls_report()
        self.assertTrue(wizard_default.sales_team_ids)
        self.assertEqual(res_default['type'], 'ir.actions.report')

    def test_get_xlsx_report(self):
        """Test get_xlsx_report generates valid XLSX binary content for users and teams."""
        wizard = self.env['commission.report'].create({
            'date': fields.Date.today(),
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
        })

        # Test Salesperson mode report generation
        user_data = {
            'date': wizard.date,
            'date_from': wizard.date_from,
            'date_to': wizard.date_to,
            'salesperson_ids': [self.user_alice.id],
            'user_commission_salesperson': [self.user_alice.name],
            'user_commission_name': [self.comm_product.name],
            'total_list': [200.0],
            'commission_list': [20.0],
        }
        mock_resp_user = MockResponse()
        wizard.get_xlsx_report(user_data, mock_resp_user)
        user_xlsx_content = mock_resp_user.stream.getvalue()
        self.assertTrue(len(user_xlsx_content) > 0)
        # Standard ZIP/XLSX header signature: b'PK\x03\x04'
        self.assertTrue(user_xlsx_content.startswith(b'PK\x03\x04'))

        # Test Sales Team mode report generation
        team_data = {
            'date': wizard.date,
            'date_from': wizard.date_from,
            'date_to': wizard.date_to,
            'sales_team_ids': [self.sales_team.id],
            'commission_sales_team': [self.sales_team.name],
            'commission_salesperson': [self.user_dave.name],
            'commission_name': [self.comm_team.name],
            'commission_total': [500.0],
            'commission': [40.0],
        }
        mock_resp_team = MockResponse()
        wizard.get_xlsx_report(team_data, mock_resp_team)
        team_xlsx_content = mock_resp_team.stream.getvalue()
        self.assertTrue(len(team_xlsx_content) > 0)
        self.assertTrue(team_xlsx_content.startswith(b'PK\x03\x04'))
