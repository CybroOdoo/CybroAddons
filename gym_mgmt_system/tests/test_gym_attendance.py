# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from datetime import date, timedelta
from odoo.exceptions import UserError

class TestGymAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestGymAttendance, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Gym Member Attendance',
            'is_gym_member': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Attendance Monthly Membership',
            'list_price': 100.0,
            'membership': True,
            'membership_date_from': date.today() - timedelta(days=5),
            'membership_date_to': date.today() + timedelta(days=25),
        })
        cls.membership = cls.env['gym.membership'].create({
            'member_id': cls.partner.id,
            'membership_scheme_id': cls.product.id,
        })
        cls.membership.action_set_active()

    def test_quick_checkin(self):
        """Test quick checkin functionality."""
        result = self.env['gym.attendance'].quick_checkin(self.partner.id)
        self.assertEqual(result['type'], 'ir.actions.client')
        
        attendance = self.env['gym.attendance'].search([('member_id', '=', self.partner.id)])
        self.assertTrue(attendance)
        self.assertEqual(attendance.state, 'checked_in')
        
        # Test check out
        attendance.action_check_out()
        self.assertEqual(attendance.state, 'checked_out')
        self.assertTrue(attendance.check_out)

    def test_already_checked_in(self):
        """Test error when checking in already checked in member."""
        self.env['gym.attendance'].quick_checkin(self.partner.id)
        
        with self.assertRaises(UserError):
            self.env['gym.attendance'].create({
                'member_id': self.partner.id
            })
