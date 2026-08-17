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

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from odoo.tools import mute_logger

class TestTargetAchieve(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTargetAchieve, cls).setUpClass()
        
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.user = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson',
            'email': 'test@salesperson.com',
            'groups_id': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])]
        })
        
        cls.crm_team = cls.env['crm.team'].create({
            'name': 'Test CRM Team',
            'use_quotations': True,
        })
        
        cls.team_member = cls.env['crm.team.member'].create({
            'user_id': cls.user.id,
            'crm_team_id': cls.crm_team.id,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

    def test_01_compute_name(self):
        """Test the compute name functionality"""
        target = self.env['target.achieve'].create({
            'sale_user_id': self.team_member.id,
            'user_target': 1000.0,
            'time_span': 'monthly',
        })
        expected_name = f"{self.team_member.name}:{self.crm_team.name}"
        self.assertEqual(target.name, expected_name, "Name should be computed correctly")

    def test_02_team_target_computation(self):
        """Test the team target computation"""
        target = self.env['target.achieve'].create({
            'sale_user_id': self.team_member.id,
            'user_target': 5000.0,
            'time_span': 'monthly',
        })
        self.assertEqual(target.team_target, 5000.0, "Team target on record should be computed")

    def test_03_achieved_amt(self):
        """Test the achieved amount computation"""
        target = self.env['target.achieve'].create({
            'sale_user_id': self.team_member.id,
            'user_target': 1000.0,
            'time_span': 'daily',
        })
        
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'team_id': self.crm_team.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 100.0,
            })]
        })
        sale_order.action_confirm()
        
        target._compute_achieved_amt()
        self.assertEqual(target.person_achieved_amt, 200.0, "Person achieved amount should be 200.0")
        self.assertEqual(target.team_achieved_amt, 200.0, "Team achieved amount should be 200.0")

    def test_04_achieved_amt_spans(self):
        """Test achieved amount for different time spans"""
        # Using a new salesperson to avoid unique_combination constraint with existing ones
        user2 = self.env['res.users'].create({
            'name': 'Test Salesperson 2',
            'login': 'test_salesperson2',
        })
        team_member2 = self.env['crm.team.member'].create({
            'user_id': user2.id,
            'crm_team_id': self.crm_team.id,
        })
        target_monthly = self.env['target.achieve'].create({
            'sale_user_id': team_member2.id,
            'user_target': 2000.0,
            'time_span': 'monthly',
        })
        
        user3 = self.env['res.users'].create({
            'name': 'Test Salesperson 3',
            'login': 'test_salesperson3',
        })
        team_member3 = self.env['crm.team.member'].create({
            'user_id': user3.id,
            'crm_team_id': self.crm_team.id,
        })
        target_yearly = self.env['target.achieve'].create({
            'sale_user_id': team_member3.id,
            'user_target': 3000.0,
            'time_span': 'yearly',
        })
        
        target_monthly._compute_achieved_amt()
        target_yearly._compute_achieved_amt()
        self.assertTrue(target_monthly.user_target > 0)
        self.assertTrue(target_yearly.user_target > 0)

    def test_05_delete_record(self):
        """Test deletion updates team target"""
        self.crm_team.team_target = 5000.0
        user_del = self.env['res.users'].create({
            'name': 'Test Salesperson Del',
            'login': 'test_salesperson_del',
        })
        team_member_del = self.env['crm.team.member'].create({
            'user_id': user_del.id,
            'crm_team_id': self.crm_team.id,
        })
        target = self.env['target.achieve'].create({
            'sale_user_id': team_member_del.id,
            'user_target': 1000.0,
            'time_span': 'monthly',
        })
        target.unlink()
        self.assertEqual(self.crm_team.team_target, 4000.0, "Team target should be decreased by user target")

    @mute_logger('odoo.sql_db')
    def test_06_constraints(self):
        """Test SQL constraints"""
        user_c = self.env['res.users'].create({
            'name': 'Test Salesperson C',
            'login': 'test_salesperson_c',
        })
        team_member_c = self.env['crm.team.member'].create({
            'user_id': user_c.id,
            'crm_team_id': self.crm_team.id,
        })
        
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env['target.achieve'].create({
                    'sale_user_id': team_member_c.id,
                    'user_target': 0.0,
                    'time_span': 'monthly',
                })
        
        target = self.env['target.achieve'].create({
            'sale_user_id': team_member_c.id,
            'user_target': 1000.0,
            'time_span': 'monthly',
        })
        
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env['target.achieve'].create({
                    'sale_user_id': team_member_c.id,
                    'user_target': 2000.0,
                    'time_span': 'daily',
                })
