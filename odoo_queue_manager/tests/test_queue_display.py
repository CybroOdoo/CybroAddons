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
from odoo.tests.common import TransactionCase


class TestQueueDisplay(TransactionCase):
    """Test suite for queue.display model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.QueueCounter = cls.env['queue.counter']
        cls.QueueDisplay = cls.env['queue.display']
        cls.TokenToken = cls.env['token.token']
        cls.Department = cls.env['department']

        cls.dept = cls.Department.create({
            'name': 'Sales',
            'code': 'SL'
        })
        cls.counter = cls.QueueCounter.create({
            'name': 'Counter A'
        })
        cls.display = cls.QueueDisplay.create({
            'name': 'Main Display',
            'counter_id': cls.counter.id
        })

    def test_compute_display_url(self):
        """Test _compute_display_url computation."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url'
        )
        expected_url = f"{base_url}/queue/display/{self.counter.id}"
        self.assertEqual(self.display.display_url, expected_url)

    def test_compute_current_token_no_token(self):
        """Test _compute_current_token when no token is in progress."""
        self.assertEqual(self.display.current_token, "No Token")

    def test_compute_current_token_in_progress(self):
        """Test _compute_current_token when a token is in progress."""
        token = self.TokenToken.create({
            'customer_name': 'John Doe',
            'department_id': self.dept.id,
            'counter_id': self.counter.id,
            'state': 'in_progress',
            'token': 'SL-001'
        })
        self.display._compute_current_token()
        self.assertEqual(self.display.current_token, 'SL-001')
