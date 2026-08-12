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


class TestQueueCounter(TransactionCase):
    """Test suite for queue.counter model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.QueueCounter = cls.env['queue.counter']
        cls.counter = cls.QueueCounter.create({
            'name': 'Counter 1'
        })

    def test_queue_counter_creation(self):
        """Test queue counter creation."""
        self.assertEqual(self.counter.name, 'Counter 1')

    def test_action_start_process(self):
        """Test action_start_process method returns expected window action dict."""
        res = self.counter.action_start_process()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('name'), 'Start Processing')
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'select.department')
        self.assertEqual(res.get('view_mode'), 'form')
        self.assertEqual(res.get('target'), 'new')
        self.assertEqual(
            res.get('context', {}).get('default_counter_id'),
            self.counter.id
        )
