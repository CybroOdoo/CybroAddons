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


class TestQueueProcess(TransactionCase):
    """Test suite for queue.process model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.QueueProcess = cls.env['queue.process']
        cls.Department = cls.env['department']
        cls.QueueCounter = cls.env['queue.counter']

        cls.dept = cls.Department.create({'name': 'Billing', 'code': 'BL'})
        cls.counter = cls.QueueCounter.create({'name': 'Counter B'})

    def test_queue_process_create(self):
        """Test record creation and reference sequence generation."""
        qp = self.QueueProcess.create({
            'counter_id': self.counter.id,
            'department_id': self.dept.id,
            'customer_name': 'Alice',
            'customer_query': 'Invoice inquiry',
            'feedback': 'Good service',
            'state': 'done'
        })
        self.assertTrue(qp.reference_no)
        self.assertEqual(qp.customer_name, 'Alice')
        self.assertEqual(qp.state, 'done')
        self.assertEqual(qp.user_id, self.env.user)

    def test_get_report_base_filename(self):
        """Test filename generation for queue process report."""
        qp = self.QueueProcess.create({
            'counter_id': self.counter.id,
            'department_id': self.dept.id,
            'customer_name': 'Bob'
        })
        expected_name = f"Queue Process - {qp.reference_no}"
        self.assertEqual(qp._get_report_base_filename(), expected_name)
