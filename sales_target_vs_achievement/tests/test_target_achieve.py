# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date, datetime
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

# The achieved amount depends on today's date, so the tests freeze it.
FIXED_TODAY = date(2026, 6, 15)
TODAY_DT = datetime(2026, 6, 15, 10, 0)
THIS_MONTH_DT = datetime(2026, 6, 2, 10, 0)
THIS_YEAR_DT = datetime(2026, 2, 10, 10, 0)
LAST_YEAR_DT = datetime(2025, 12, 31, 10, 0)


class TestTargetAchieve(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.group_salesman = cls.env.ref('sales_team.group_sale_salesman')
        cls.group_manager = cls.env.ref('sales_team.group_sale_manager')
        cls.group_target_user = cls.env.ref(
            'sales_target_vs_achievement.group_sales_target_user')
        cls.group_target_admin = cls.env.ref(
            'sales_target_vs_achievement.group_sales_target_admin')

        cls.user = cls._create_user('Test Salesperson', 'test_salesperson')
        cls.crm_team = cls.env['crm.team'].create({'name': 'Test CRM Team'})
        cls.team_member = cls.env['crm.team.member'].create({
            'user_id': cls.user.id,
            'crm_team_id': cls.crm_team.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})

    @classmethod
    def _create_user(cls, name, login, groups=None):
        groups = groups or cls.group_salesman
        return cls.env['res.users'].create({
            'name': name,
            'login': login,
            'email': f'{login}@example.com',
            'group_ids': [Command.set(groups.ids)],
        })

    def _create_member(self, name, login, team=None):
        user = self._create_user(name, login)
        member = self.env['crm.team.member'].create({
            'user_id': user.id,
            'crm_team_id': (team or self.crm_team).id,
        })
        return user, member

    def _create_target(self, member, amount=1000.0, span='monthly'):
        return self.env['target.achieve'].create({
            'sale_user_id': member.id,
            'user_target': amount,
            'time_span': span,
        })

    def _create_order(self, user, team=None, qty=1, date_order=TODAY_DT,
                      confirm=True):
        """Create a sales order worth ``qty * 100`` (taxes removed)."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': user.id,
            'team_id': (team or self.crm_team).id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': qty,
                'price_unit': 100.0,
                'tax_ids': [Command.clear()],
            })],
        })
        if confirm:
            order.action_confirm()
            order.date_order = date_order
        return order

    def _compute_achieved(self, target):
        with patch.object(fields.Date, 'today', return_value=FIXED_TODAY):
            target._compute_person_achieved_amt()
            target._compute_team_achieved_amt()

    def test_01_compute_name(self):
        """Test the compute name functionality"""
        target = self._create_target(self.team_member)
        expected_name = f"{self.team_member.name}:{self.crm_team.name}"
        self.assertEqual(target.name, expected_name,
                         "Name should be computed correctly")

    def test_02_team_target_computation(self):
        """Test the team target computation for a single target"""
        target = self._create_target(self.team_member, 5000.0)
        self.assertEqual(target.team_target, 5000.0,
                         "Team target on record should be computed")

    def test_03_team_target_multiple_members(self):
        """The Sales Team target is the sum of its members' targets"""
        _user2, member2 = self._create_member(
            'Test Salesperson 2', 'test_salesperson2')
        self._create_target(self.team_member, 5000.0)
        self._create_target(member2, 3000.0)
        self.assertEqual(self.crm_team.team_target, 8000.0,
                         "Sales Team target should be the sum of all targets")

    def test_04_achieved_amt_daily(self):
        """Test the achieved amount computation for a daily target"""
        self._create_order(self.user, qty=2)
        target = self._create_target(self.team_member, span='daily')
        self._compute_achieved(target)
        self.assertEqual(target.person_achieved_amt, 200.0)
        self.assertEqual(target.team_achieved_amt, 200.0)

    def test_05_achieved_amt_spans(self):
        """Orders are counted only inside the selected time span"""
        self._create_order(self.user, qty=1, date_order=TODAY_DT)
        self._create_order(self.user, qty=2, date_order=THIS_MONTH_DT)
        self._create_order(self.user, qty=3, date_order=THIS_YEAR_DT)
        self._create_order(self.user, qty=4, date_order=LAST_YEAR_DT)
        target = self._create_target(self.team_member)
        for span, expected in (('daily', 100.0),
                               ('monthly', 300.0),
                               ('yearly', 600.0)):
            with self.subTest(span=span):
                target.time_span = span
                self._compute_achieved(target)
                self.assertEqual(target.person_achieved_amt, expected)
                self.assertEqual(target.team_achieved_amt, expected)

    def test_06_achieved_amt_filters(self):
        """Only confirmed orders of the right salesperson and team count"""
        other_team = self.env['crm.team'].create({'name': 'Other CRM Team'})
        user2, _member2 = self._create_member(
            'Test Salesperson 2', 'test_salesperson2')
        # Counts for the person and for the team.
        self._create_order(self.user, qty=1)
        # Counts only for the team (another salesperson, same team).
        self._create_order(user2, qty=2)
        # Counts only for the person (same salesperson, another team).
        self._create_order(self.user, team=other_team, qty=3)
        # Never counted: the order is not confirmed.
        self._create_order(self.user, qty=5, confirm=False)
        target = self._create_target(self.team_member, span='daily')
        self._compute_achieved(target)
        self.assertEqual(target.person_achieved_amt, 400.0)
        self.assertEqual(target.team_achieved_amt, 300.0)

    def test_07_delete_record(self):
        """Test deletion updates team target"""
        self._create_target(self.team_member, 4000.0)
        _user, member = self._create_member(
            'Test Salesperson Del', 'test_salesperson_del')
        target = self._create_target(member, 1000.0)
        self.assertEqual(self.crm_team.team_target, 5000.0)
        target.unlink()
        self.assertEqual(self.crm_team.team_target, 4000.0,
                         "Team target should be decreased by user target")

    def test_11_team_achieved_amt_follows_orders(self):
        """The stored team achieved amount follows the team's sales orders"""
        target = self._create_target(self.team_member, span='daily')
        self.assertEqual(target.team_achieved_amt, 0.0)
        order = self._create_order(
            self.user, qty=2, date_order=fields.Datetime.now())
        self.assertEqual(target.team_achieved_amt, 200.0,
                         "A confirmed order should be counted automatically")
        order.order_line.product_uom_qty = 3
        self.assertEqual(target.team_achieved_amt, 300.0,
                         "A changed order amount should be counted")
        order._action_cancel()
        self.assertEqual(target.team_achieved_amt, 0.0,
                         "A cancelled order should no longer be counted")

    @mute_logger('odoo.sql_db')
    def test_08_constraints(self):
        """Test the unique and positive target constraints"""
        _user, member = self._create_member('Test Salesperson C',
                                            'test_salesperson_c')
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._create_target(member, 0.0)
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._create_target(member, -10.0)

        self._create_target(member, 1000.0)
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._create_target(member, 2000.0, 'daily')

    def test_09_access_rights(self):
        """Target users can only read, target admins have full access"""
        target_user = self._create_user(
            'Target User', 'target_user',
            self.group_salesman | self.group_target_user)
        target_admin = self._create_user(
            'Target Admin', 'target_admin',
            self.group_manager | self.group_target_admin)
        _user2, member2 = self._create_member(
            'Test Salesperson 2', 'test_salesperson2')
        target = self._create_target(self.team_member, 1000.0)
        vals = {
            'sale_user_id': member2.id,
            'user_target': 2000.0,
            'time_span': 'monthly',
        }

        as_user = target.with_user(target_user)
        self.assertEqual(as_user.user_target, 1000.0)
        with self.assertRaises(AccessError):
            as_user.write({'user_target': 1500.0})
        with self.assertRaises(AccessError):
            as_user.unlink()
        with self.assertRaises(AccessError):
            self.env['target.achieve'].with_user(target_user).create(vals)

        new_target = self.env['target.achieve'].with_user(
            target_admin).create(vals)
        new_target.write({'user_target': 3000.0})
        self.assertEqual(new_target.user_target, 3000.0)
        new_target.unlink()
        self.assertFalse(new_target.exists())

    def test_10_views(self):
        """The module views and the Sales Team form extension load"""
        team_form = self.env['crm.team'].get_view(view_type='form')
        self.assertIn('team_target', team_form['arch'])
        for view_type in ('list', 'form', 'search', 'graph'):
            with self.subTest(view_type=view_type):
                self.env['target.achieve'].get_view(view_type=view_type)
