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
from types import SimpleNamespace

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMealsPlanning(TransactionCase):
    """Tests for the time-based product plans (meals.planning)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.planning = cls.env['meals.planning']
        cls.product = cls.env['product.product'].create({
            'name': 'Plan Test Coffee',
            'available_in_pos': True,
        })

    def _create_plan(self, **values):
        vals = {
            'name': 'Breakfast',
            'time_from': 7.0,
            'time_to': 11.0,
            'menu_product_ids': [(6, 0, self.product.ids)],
        }
        vals.update(values)
        return self.planning.create(vals)

    def test_default_state_is_deactivated(self):
        """A new plan must start as deactivated"""
        plan = self._create_plan()
        self.assertEqual(plan.state, 'deactivated')

    def test_valid_time_range(self):
        """A normal range inside one day is accepted"""
        plan = self._create_plan(time_from=6.5, time_to=10.25)
        self.assertEqual(plan.time_from, 6.5)
        self.assertEqual(plan.time_to, 10.25)

    def test_range_crossing_midnight_is_allowed(self):
        """A range such as 22:00 to 02:00 is accepted"""
        plan = self._create_plan(time_from=22.0, time_to=2.0)
        self.assertEqual(plan.time_from, 22.0)
        self.assertEqual(plan.time_to, 2.0)

    def test_full_day_boundaries_are_allowed(self):
        """00:00 and 24:00 are valid limits"""
        plan = self._create_plan(time_from=0.0, time_to=24.0)
        self.assertEqual(plan.time_to, 24.0)

    def test_equal_times_are_rejected(self):
        """From and To must be different"""
        with self.assertRaises(ValidationError):
            self._create_plan(time_from=9.0, time_to=9.0)

    def test_time_above_24_is_rejected(self):
        """Values greater than 24:00 are not valid"""
        with self.assertRaises(ValidationError):
            self._create_plan(time_from=8.0, time_to=24.5)
        with self.assertRaises(ValidationError):
            self._create_plan(time_from=25.0, time_to=10.0)

    def test_negative_time_is_rejected(self):
        """Negative values are not valid"""
        with self.assertRaises(ValidationError):
            self._create_plan(time_from=-1.0, time_to=10.0)

    def test_constraint_works_on_multiple_records(self):
        """The constraint must loop over every record of the recordset"""
        plans = self._create_plan(name='Plan A') | self._create_plan(
            name='Plan B')
        plans.write({'time_from': 8.0, 'time_to': 9.0})
        self.assertEqual(plans.mapped('time_from'), [8.0, 8.0])
        with self.assertRaises(ValidationError):
            plans.write({'time_from': 9.0, 'time_to': 9.0})

    def test_activate_and_deactivate(self):
        """The buttons change the state of every selected plan"""
        plans = self._create_plan(name='Plan A') | self._create_plan(
            name='Plan B')
        plans.action_activate_meals_plan()
        self.assertEqual(set(plans.mapped('state')), {'activated'})
        plans.action_deactivate_meals_plan()
        self.assertEqual(set(plans.mapped('state')), {'deactivated'})

    def test_load_pos_data_fields(self):
        """The POS receives the fields needed to filter the products"""
        fields_to_load = self.planning._load_pos_data_fields(False)
        for field_name in ('name', 'menu_product_ids', 'time_from',
                           'time_to', 'state'):
            self.assertIn(field_name, fields_to_load)

    def test_load_pos_data_domain_with_session(self):
        """Only plans of the opened Point of Sale are loaded"""
        config = SimpleNamespace(ids=[42])
        session = SimpleNamespace(config_id=config)
        domain = self.planning._load_pos_data_domain({'pos.session': session})
        self.assertEqual(domain, [('pos_config_ids', 'in', [42])])

    def test_load_pos_data_domain_without_session(self):
        """Without a session no extra filter is applied"""
        self.assertEqual(self.planning._load_pos_data_domain({}), [])

    def test_pos_session_loads_meals_planning(self):
        """meals.planning is added to the models loaded in the POS"""
        models_to_load = self.env['pos.session']._load_pos_data_models(
            self.env['pos.config'])
        self.assertIn('meals.planning', models_to_load)
