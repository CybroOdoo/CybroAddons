# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestOdooQueueManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Department
        cls.department = cls.env['department'].create({
            'name': 'Customer Support',
            'code': 'CS'
        })
        # Counter
        cls.counter = cls.env['queue.counter'].create({
            'name': 'Counter 1',
        })
        # Token Interface
        cls.interface = cls.env['token.interface'].create({
            'name': 'Morning Session',
        })

    def test_token_generation(self):
        """Test token and reference generation."""
        token = self.env['token.token'].create({
            'customer_name': 'Demo Customer',
            'department_id': self.department.id,
            'mobile': '9876543210',
        })
        self.assertTrue(token.reference_no)
        self.assertTrue(token.token)
        self.assertNotEqual(
            token.reference_no,
            'New'
        )

    def test_token_session_generation(self):
        """Test token session sequence generation."""
        session = self.env['token.session'].create({
            'name': 'Morning Session',
        })
        self.assertTrue(session.reference_no)
        self.assertNotEqual(
            session.reference_no,
            'New'
        )

    def test_start_new_session(self):
        """Test starting a token session."""
        action = self.interface.action_start_new_session()
        self.assertTrue(
            self.interface.is_start_session
        )
        self.assertEqual(
            action['type'],
            'ir.actions.act_url'
        )
        self.assertEqual(
            action['url'],
            '/generate/token'
        )

    def test_close_session(self):
        """Test closing token session."""
        self.interface.is_start_session = True
        self.interface.action_close_session()
        self.assertFalse(
            self.interface.is_start_session
        )

    def test_queue_display_url(self):
        """Test display URL computation."""
        display = self.env['queue.display'].create({
            'name': 'Display Screen',
            'counter_id': self.counter.id,
        })
        self.assertIn(
            f'/queue/display/{self.counter.id}',
            display.display_url
        )

    def test_current_token(self):
        """Test current token computation."""
        token = self.env['token.token'].create({
            'customer_name': 'Customer',
            'department_id': self.department.id,
            'counter_id': self.counter.id,
            'state': 'in_progress',
        })
        display = self.env['queue.display'].create({
            'name': 'Display',
            'counter_id': self.counter.id,
        })
        display._compute_current_token()
        self.assertEqual(
            display.current_token,
            token.token
        )

    def test_queue_process_reference(self):
        """Test queue process sequence generation."""
        process = self.env['queue.process'].create({
            'department_id': self.department.id,
            'customer_name': 'Customer',
        })
        self.assertTrue(process.reference_no)
        self.assertNotEqual(
            process.reference_no,
            'New'
        )

    def test_select_department_action(self):
        """Test department selection wizard action."""
        wizard = self.env['select.department'].create({
            'department_id': self.department.id,
            'counter_id': self.counter.id,
        })
        action = wizard.action_submit()
        self.assertEqual(
            action['type'],
            'ir.actions.act_url'
        )
        self.assertIn(
            f'/queue/counter/{self.department.id}/{self.counter.id}',
            action['url']
        )
