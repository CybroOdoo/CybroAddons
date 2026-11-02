# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from datetime import date, timedelta
from odoo.tests.common import TransactionCase


class TestMachineWorkorder(TransactionCase):
    """Test cases for the MachineWorkOrder model (machine.workorder)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Workorder Customer',
        })
        cls.today = date.today()
        cls.service = cls.env['machine.service'].create({
            'name': 'General Maintenance',
        })
        cls.repair = cls.env['machine.repair'].create({
            'name': 'Base Repair for WO',
            'customer_id': cls.partner.id,
            'priority': 'normal',
            'repair_detail': 'Routine check.',
            'repair_req_date': cls.today,
        })

    # ------------------------------------------------------------------
    # 1. Basic creation
    # ------------------------------------------------------------------
    def test_01_create_workorder(self):
        """A work order can be created with minimal fields."""
        wo = self.env['machine.workorder'].create({
            'customer_id': self.partner.id,
            'date': self.today,
            'priority': 'normal',
            'repair_id': self.repair.id,
        })
        self.assertTrue(wo.exists())
        self.assertEqual(wo.customer_id.id, self.partner.id)

    def test_02_workorder_priority_stored(self):
        """Priority field value is stored and retrievable."""
        for prio in ('high', 'normal', 'low'):
            wo = self.env['machine.workorder'].create({
                'customer_id': self.partner.id,
                'date': self.today,
                'priority': prio,
            })
            self.assertEqual(wo.priority, prio)

    def test_03_workorder_linked_to_repair(self):
        """A work order created via action_create_work_order links to the repair."""
        result = self.repair.action_create_work_order()
        wo = self.env['machine.workorder'].browse(result['res_id'])
        self.assertEqual(wo.repair_id.id, self.repair.id)

    # ------------------------------------------------------------------
    # 2. Work order action response
    # ------------------------------------------------------------------
    def test_04_action_create_work_order_returns_window(self):
        """action_create_work_order() must return an ir.actions.act_window."""
        result = self.repair.action_create_work_order()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'machine.workorder')
        self.assertEqual(result['view_mode'], 'form')

    # ------------------------------------------------------------------
    # 3. Date fields
    # ------------------------------------------------------------------
    def test_05_workorder_date_fields(self):
        """All date fields on a work order can be set and stored."""
        start = self.today
        end = self.today + timedelta(days=3)
        wo = self.env['machine.workorder'].create({
            'customer_id': self.partner.id,
            'date': self.today,
            'priority': 'normal',
            'scheduled_date': start,
            'planned_end_date': end,
            'start_date': start,
            'end_date': end,
        })
        self.assertEqual(wo.scheduled_date, start)
        self.assertEqual(wo.planned_end_date, end)
        self.assertEqual(wo.start_date, start)
        self.assertEqual(wo.end_date, end)

    # ------------------------------------------------------------------
    # 4. Numeric fields
    # ------------------------------------------------------------------
    def test_06_workorder_duration_and_hours(self):
        """Duration and hours_worked fields accept float values."""
        wo = self.env['machine.workorder'].create({
            'customer_id': self.partner.id,
            'date': self.today,
            'priority': 'high',
            'duration': 4.5,
            'hours_worked': 3.75,
        })
        self.assertAlmostEqual(wo.duration, 4.5)
        self.assertAlmostEqual(wo.hours_worked, 3.75)

    # ------------------------------------------------------------------
    # 5. Work order service link
    # ------------------------------------------------------------------
    def test_07_workorder_linked_to_service(self):
        """work_order_id field links to machine.service correctly."""
        wo = self.env['machine.workorder'].create({
            'customer_id': self.partner.id,
            'date': self.today,
            'priority': 'normal',
            'work_order_id': self.service.id,
        })
        self.assertEqual(wo.work_order_id.id, self.service.id)
        self.assertEqual(wo.work_order_id.name, 'General Maintenance')

    # ------------------------------------------------------------------
    # 6. Smart button action from repair
    # ------------------------------------------------------------------
    def test_08_get_machine_workorder_action_filters_by_repair(self):
        """get_machine_workorder() domain should filter by repair id."""
        action = self.repair.get_machine_workorder()
        domain = action.get('domain', [])
        self.assertIn(('repair_id', '=', self.repair.id), domain)

    # ------------------------------------------------------------------
    # 7. Multiple workorders per repair
    # ------------------------------------------------------------------
    def test_09_multiple_workorders_per_repair(self):
        """Multiple work orders can be linked to the same repair."""
        for i in range(3):
            self.env['machine.workorder'].create({
                'customer_id': self.partner.id,
                'date': self.today,
                'priority': 'normal',
                'repair_id': self.repair.id,
            })
        count = self.env['machine.workorder'].search_count(
            [('repair_id', '=', self.repair.id)]
        )
        self.assertGreaterEqual(count, 3)
