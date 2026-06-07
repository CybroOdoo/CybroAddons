# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestMealsPlanning(TransactionCase):
    def setUp(self):
        super(TestMealsPlanning, self).setUp()
        # Create dependencies for PoS Session
        vals = {'name': 'Test POS'}
        if 'self_ordering_mode' in self.env['pos.config']._fields:
            vals['self_ordering_mode'] = 'nothing'
        self.pos_config = self.env['pos.config'].create(vals)
        # Create a PoS Session
        self.pos_session = self.env['pos.session'].create({
            'user_id': self.env.uid,
            'config_id': self.pos_config.id,
        })
        # Create a product available in PoS
        self.product = self.env['product.product'].create({
            'name': 'Test Meal',
            'available_in_pos': True,
        })

    def test_meal_planning_flow(self):
        """Test the full lifecycle of a meals plan (Create -> Activate -> Deactivate)"""
        # Create a valid meals planning record
        plan = self.env['meals.planning'].create({
            'name': 'Lunch Plan',
            'pos_ids': [(4, self.pos_session.id)],
            'time_from': 12.0,
            'time_to': 14.0,
            'menu_product_ids': [(4, self.product.id)],
        })
        # 1. Verify default state is deactivated
        self.assertEqual(plan.state, 'deactivated', "Initial state should be deactivated")
        # 2. Test activation
        plan.action_activate_meals_plan()
        self.assertEqual(plan.state, 'activated', "State should be activated after action_activate")
        # 3. Test deactivation
        plan.action_deactivate_meals_plan()
        self.assertEqual(plan.state, 'deactivated', "State should be deactivated after action_deactivate")

    def test_time_range_constraints(self):
        """Test the time validation constraints"""
        # 1. Test 'From' time >= 'To' time (Should raise ValidationError)
        with self.assertRaisesRegex(ValidationError, 'From time must be less than to time!'):
            self.env['meals.planning'].create({
                'name': 'Invalid range',
                'pos_ids': [(4, self.pos_session.id)],
                'time_from': 15.0,
                'time_to': 12.0,
            })
        # 2. Test time value > 24 (Should raise ValidationError)
        with self.assertRaisesRegex(ValidationError, 'Time value greater than 24 is not valid!'):
            self.env['meals.planning'].create({
                'name': 'Invalid hour',
                'pos_ids': [(4, self.pos_session.id)],
                'time_from': 1.0,
                'time_to': 25.0,
            })

    def test_pos_data_loading_domain(self):
        """Test the domain logic for loading data into the POS frontend"""
        # Create a dinner plan
        self.env['meals.planning'].create({
            'name': 'Dinner Plan',
            'pos_ids': [(4, self.pos_session.id)],
            'time_from': 18.0,
            'time_to': 20.0,
        })
        # Mock the data structure that the POS loader sends to the server
        mock_data = {
            'pos.session': [{'id': self.pos_session.id}]
        }
        # Check if _load_pos_data_domain returns the expected domain for the current session
        domain = self.env['meals.planning']._load_pos_data_domain(
            mock_data, 
            self.pos_config
        )
        # Verify that the session filtering is correct
        self.assertIn(('pos_ids', 'in', [self.pos_session.id]), domain, 
                      "The loaded data should be filtered by the current PoS Session ID")
