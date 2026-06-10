# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from datetime import date, timedelta
from odoo.exceptions import UserError

class TestGymMembershipExtension(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestGymMembershipExtension, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Extension Member',
            'is_gym_member': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Monthly Extension Plan',
            'list_price': 100.0,
            'membership': True,
            'membership_date_from': date.today(),
            'membership_date_to': date.today() + timedelta(days=30),
        })
        cls.membership = cls.env['gym.membership'].create({
            'member_id': cls.partner.id,
            'membership_scheme_id': cls.product.id,
        })
        cls.membership.action_set_active()
        # Need to expire to extend it
        cls.membership.action_expire()

    def test_wizard_same_plan_extension(self):
        """Test extending membership with same plan via wizard."""
        wizard = self.env['gym.membership.extend'].create({
            'membership_id': self.membership.id,
            'member_id': self.partner.id,
            'extension_type': 'same_plan'
        })
        
        # Verify the computed days and amount
        self.assertEqual(wizard.extension_days, 30)
        self.assertEqual(wizard.extension_amount, 100.0)
        
        # Trigger the action to extend
        action = wizard.action_extend_membership()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'sale.order')
        
        # Verify the extension applied properly on the membership
        self.assertEqual(self.membership.state, 'active')
        self.assertEqual(self.membership.total_extended_days, 30)
