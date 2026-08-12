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


class TestSelectDepartmentWizard(TransactionCase):
    """Test suite for select.department wizard model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env['department']
        cls.QueueCounter = cls.env['queue.counter']
        cls.SelectDepartment = cls.env['select.department']

        cls.dept = cls.Department.create({'name': 'Help Desk', 'code': 'HD'})
        cls.counter = cls.QueueCounter.create({'name': 'Counter 3'})

    def test_action_submit(self):
        """Test action_submit returns act_url dict with department and counter IDs."""
        wizard = self.SelectDepartment.create({
            'department_id': self.dept.id,
            'counter_id': self.counter.id
        })
        res = wizard.action_submit()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('target'), 'new')
        expected_url = f'/queue/counter/{self.dept.id}/{self.counter.id}'
        self.assertEqual(res.get('url'), expected_url)
