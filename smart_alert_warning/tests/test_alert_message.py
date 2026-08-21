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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestAlertMessage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.partner_view = cls.env['ir.ui.view'].search([('model', '=', 'res.partner'), ('type', '=', 'form')], limit=1)
        
        # If no partner view exists in the test DB, create a basic one
        if not cls.partner_view:
            cls.partner_view = cls.env['ir.ui.view'].create({
                'name': 'res.partner.form.test',
                'model': 'res.partner',
                'type': 'form',
                'arch': '<form><sheet></sheet></form>'
            })
            
        cls.test_group = cls.env.ref('base.group_user')

    def test_01_initial_state(self):
        """Test initial state of alert.message is 'draft'"""
        alert = self.env['alert.message'].create({
            'name': 'Test Alert 1',
            'document_type_id': self.partner_model.id,
            'alert_messages': 'This is a test warning!',
            'type': 'alert-warning',
            'view_id': self.partner_view.id,
        })
        self.assertEqual(alert.state, 'draft')
        self.assertFalse(alert.new_view_id)

    def test_02_action_apply_no_group_no_filter(self):
        """Test action_apply with no group and empty filter"""
        alert = self.env['alert.message'].create({
            'name': 'Test Alert 2',
            'document_type_id': self.partner_model.id,
            'alert_messages': 'No filter message',
            'type': 'alert-info',
            'view_id': self.partner_view.id,
            'field_filter': '[]',
        })
        alert.action_apply()
        self.assertEqual(alert.state, 'done')
        self.assertTrue(alert.new_view_id)
        
        # Check generated arch
        arch = alert.new_view_id.arch
        self.assertIn('class="alert alert-info"', arch)
        self.assertIn('No filter message', arch)
        self.assertNotIn('groups=', arch)
        self.assertNotIn('invisible=', arch)

    def test_03_action_apply_with_group_no_filter(self):
        """Test action_apply with a group and empty filter"""
        alert = self.env['alert.message'].create({
            'name': 'Test Alert 3',
            'document_type_id': self.partner_model.id,
            'alert_messages': 'Group message',
            'type': 'alert-success',
            'view_id': self.partner_view.id,
            'group_id': self.test_group.id,
            'field_filter': '[]',
        })
        alert.action_apply()
        self.assertEqual(alert.state, 'done')
        self.assertTrue(alert.new_view_id)
        
        # Get XML ID of group to verify it is in groups attribute
        xml_ids = self.test_group.get_external_id()
        expected_xml_id = xml_ids.get(self.test_group.id)
        
        arch = alert.new_view_id.arch
        self.assertIn('groups="%s"' % expected_xml_id, arch)
        self.assertNotIn('invisible=', arch)

    def test_04_action_apply_operators(self):
        """Test how different filter operators translate in action_apply"""
        operators_tests = [
            ('=', 'name', 'test', 'invisible=" name != &quot;test&quot;"'),
            ('!=', 'name', 'test', 'invisible=" name == &quot;test&quot;"'),
            ('>', 'id', 5, 'invisible=" id &lt; 5"'),
            ('<', 'id', 5, 'invisible=" id &gt; 5"'),
            ('>=', 'id', 5, 'invisible=" id &lt;= 5"'),
            ('<=', 'id', 5, 'invisible=" id &gt;= 5"'),
            ('ilike', 'name', 'test', 'invisible=" name not in [&quot;test&quot;]"'),
            ('not ilike', 'name', 'test', 'invisible=" name in [&quot;test&quot;]"'),
            ('in', 'id', [1, 2], 'invisible=" id not in [1, 2]"'),
            ('not in', 'id', [1, 2], 'invisible=" id in [1, 2]"'),
        ]

        for operator, field_name, value, expected_invisible_str in operators_tests:
            # Safe descriptive label for the operator to avoid literal XML angle brackets
            safe_operator_name = operator.replace('<', 'LT').replace('>', 'GT')
            
            with self.subTest(operator=operator):
                alert = self.env['alert.message'].create({
                    'name': 'Test Operator %s' % safe_operator_name,
                    'document_type_id': self.partner_model.id,
                    'alert_messages': 'Safe alert message for operator %s' % safe_operator_name,
                    'type': 'alert-primary',
                    'view_id': self.partner_view.id,
                    'field_filter': str([(field_name, operator, value)]),
                })
                alert.action_apply()
                self.assertEqual(alert.state, 'done')
                self.assertTrue(alert.new_view_id)
                
                arch = alert.new_view_id.arch
                self.assertIn(expected_invisible_str, arch)

    def test_05_action_cancel(self):
        """Test action_cancel unlinks view and changes state"""
        alert = self.env['alert.message'].create({
            'name': 'Test Cancel Alert',
            'document_type_id': self.partner_model.id,
            'alert_messages': 'Cancel test',
            'type': 'alert-danger',
            'view_id': self.partner_view.id,
        })
        alert.action_apply()
        new_view = alert.new_view_id
        self.assertTrue(new_view.exists())
        
        alert.action_cancel()
        self.assertEqual(alert.state, 'cancelled')
        self.assertFalse(new_view.exists())

    def test_06_reset_draft(self):
        """Test reset_draft resets state back to draft"""
        alert = self.env['alert.message'].create({
            'name': 'Test Reset Alert',
            'document_type_id': self.partner_model.id,
            'alert_messages': 'Reset test',
            'type': 'alert-warning',
            'view_id': self.partner_view.id,
        })
        alert.action_apply()
        alert.action_cancel()
        self.assertEqual(alert.state, 'cancelled')
        
        alert.reset_draft()
        self.assertEqual(alert.state, 'draft')

    def test_07_action_apply_invalid_view(self):
        """Test that UserError is raised if Odoo cannot create the view"""
        # Set view_id to a view of a different model (res.users) to trigger view creation validation failure
        users_view = self.env['ir.ui.view'].search([('model', '=', 'res.users'), ('type', '=', 'form')], limit=1)
        if users_view:
            alert = self.env['alert.message'].create({
                'name': 'Test Invalid View Alert',
                'document_type_id': self.partner_model.id,  # res.partner
                'alert_messages': 'Invalid view test',
                'type': 'alert-warning',
                'view_id': users_view.id,  # res.users view
            })
            with self.assertRaises(UserError):
                alert.action_apply()
