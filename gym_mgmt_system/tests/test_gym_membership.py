# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from datetime import date, timedelta
from odoo.exceptions import UserError

class TestGymMembership(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestGymMembership, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Gym Member',
            'is_gym_member': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Monthly Membership',
            'list_price': 100.0,
            'membership': True,
            'membership_date_from': date.today(),
            'membership_date_to': date.today() + timedelta(days=30),
        })
        cls.membership = cls.env['gym.membership'].create({
            'member_id': cls.partner.id,
            'membership_scheme_id': cls.product.id,
        })

    def test_membership_creation(self):
        """Test if membership is created properly."""
        self.assertEqual(self.membership.state, 'draft')
        self.assertEqual(self.membership.membership_duration, 31)

    def test_action_confirm(self):
        """Test confirm action."""
        self.membership.action_confirm()
        self.assertEqual(self.membership.state, 'confirm')

    def test_action_set_active(self):
        """Test setting active."""
        self.membership.action_set_active()
        self.assertEqual(self.membership.state, 'active')

    def test_action_pause_and_resume(self):
        """Test pausing and resuming membership."""
        self.membership.action_set_active()
        self.membership.action_pause()
        self.assertEqual(self.membership.state, 'paused')
        self.assertTrue(self.membership.current_pause_start)
        
        self.membership.action_resume()
        self.assertEqual(self.membership.state, 'active')
        self.assertFalse(self.membership.current_pause_start)

    def test_action_expire(self):
        """Test expiring membership."""
        self.membership.action_expire()
        self.assertEqual(self.membership.state, 'expired')

    def test_action_cancel(self):
        """Test cancelling membership."""
        self.membership.action_cancel()
        self.assertEqual(self.membership.state, 'cancelled')
