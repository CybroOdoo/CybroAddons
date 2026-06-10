# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestWorkoutPlan(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestWorkoutPlan, cls).setUpClass()
        cls.workout_plan = cls.env['workout.plan'].create({
            'name': 'Test Workout Plan'
        })

    def test_action_workout_plan(self):
        """Test assign workout action."""
        action = self.workout_plan.action_workout_plan()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'assign.workout')
