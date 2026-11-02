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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestMachineRepair(TransactionCase):
    """Test cases for the MachineRepair model (machine.repair)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
            'phone': '1234567890',
        })
        # Create an employee to act as technician
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Technician',
            'work_email': 'tech@example.com',
        })
        # Common repair values
        cls.repair_vals = {
            'name': 'Test Repair Request',
            'customer_id': cls.partner.id,
            'priority': 'normal',
            'repair_detail': 'Machine is not working properly.',
        }

    # ------------------------------------------------------------------
    # 1. Creation & sequence generation
    # ------------------------------------------------------------------
    def test_01_create_repair_sequence_generated(self):
        """A new repair record should receive a sequence number (not 'New')."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.assertNotEqual(repair.repair_seq, 'New',
                            "repair_seq must be set by the sequence on create.")
        self.assertTrue(repair.repair_seq,
                        "repair_seq should not be empty after creation.")

    def test_02_create_repair_default_state_new(self):
        """Default state of a newly created repair should be 'new'."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.assertEqual(repair.state, 'new',
                         "Default state should be 'new'.")

    def test_03_create_repair_required_fields(self):
        """Creating a repair without required fields should raise an error."""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['machine.repair'].create({
                'name': 'Missing Customer',
                'priority': 'high',
                'repair_detail': 'Some detail',
                # customer_id is missing — required
            })

    # ------------------------------------------------------------------
    # 2. Date constraint
    # ------------------------------------------------------------------
    def test_04_date_constraint_closing_before_request(self):
        """Closing date must not be before repair request date."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        today = date.today()
        with self.assertRaises(ValidationError):
            repair.write({
                'repair_req_date': today,
                'closing_date': today - timedelta(days=1),
            })

    def test_05_date_constraint_valid_dates(self):
        """Valid date range (closing_date >= repair_req_date) should not raise."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        today = date.today()
        # Should NOT raise
        repair.write({
            'repair_req_date': today,
            'closing_date': today + timedelta(days=5),
        })
        self.assertEqual(repair.closing_date, today + timedelta(days=5))

    def test_06_date_constraint_same_date(self):
        """Closing date equal to repair request date should be accepted."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        today = date.today()
        repair.write({
            'repair_req_date': today,
            'closing_date': today,
        })
        self.assertEqual(repair.closing_date, today)

    # ------------------------------------------------------------------
    # 3. State transitions
    # ------------------------------------------------------------------
    def test_07_action_reopen(self):
        """action_reopen() should set state to 'reopen'."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        repair.action_reopen()
        self.assertEqual(repair.state, 'reopen')

    def test_08_action_close_repairing(self):
        """action_close_repairing() should set state to 'closed'."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        repair.action_close_repairing()
        self.assertEqual(repair.state, 'closed')

    def test_09_action_assign_teams_no_team_raises(self):
        """action_assign_teams() without a team should raise ValidationError."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        with self.assertRaises(ValidationError):
            repair.action_assign_teams()

    def test_10_action_assign_teams_with_team(self):
        """action_assign_teams() with a valid team should set state to 'assigned'."""
        team_lead = self.env['hr.employee'].create({'name': 'Team Lead'})
        team = self.env['repair.team'].create({
            'team_name': 'Alpha Team',
            'team_lead_id': team_lead.id,
        })
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'repair_team_id': team.id,
        })
        repair.action_assign_teams()
        self.assertEqual(repair.state, 'assigned')
        self.assertTrue(repair.is_team_assigned)

    # ------------------------------------------------------------------
    # 4. action_create_diagnosis
    # ------------------------------------------------------------------
    def test_11_create_diagnosis_without_closing_date_raises(self):
        """action_create_diagnosis() must raise if closing_date is not set."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        with self.assertRaises(ValidationError):
            repair.action_create_diagnosis()

    def test_12_create_diagnosis_with_closing_date(self):
        """action_create_diagnosis() should create a machine.diagnosis record."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'repair_req_date': date.today(),
            'closing_date': date.today() + timedelta(days=7),
        })
        result = repair.action_create_diagnosis()
        self.assertEqual(result['res_model'], 'machine.diagnosis')
        diagnosis = self.env['machine.diagnosis'].browse(result['res_id'])
        self.assertTrue(diagnosis.exists())
        self.assertEqual(diagnosis.machine_repair_ref_id.id, repair.id)
        self.assertEqual(diagnosis.customer_id.id, self.partner.id)

    # ------------------------------------------------------------------
    # 5. action_create_work_order
    # ------------------------------------------------------------------
    def test_13_create_work_order(self):
        """action_create_work_order() should create a machine.workorder record."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'repair_req_date': date.today(),
        })
        result = repair.action_create_work_order()
        self.assertEqual(result['res_model'], 'machine.workorder')
        workorder = self.env['machine.workorder'].browse(result['res_id'])
        self.assertTrue(workorder.exists())
        self.assertEqual(workorder.repair_id.id, repair.id)
        self.assertEqual(workorder.customer_id.id, self.partner.id)

    # ------------------------------------------------------------------
    # 6. Smart button windows
    # ------------------------------------------------------------------
    def test_14_get_machine_diagnosis_action(self):
        """get_machine_diagnosis() should return an act_window for machine.diagnosis."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        action = repair.get_machine_diagnosis()
        self.assertEqual(action['res_model'], 'machine.diagnosis')
        self.assertEqual(action['type'], 'ir.actions.act_window')

    def test_15_get_machine_workorder_action(self):
        """get_machine_workorder() should return an act_window for machine.workorder."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        action = repair.get_machine_workorder()
        self.assertEqual(action['res_model'], 'machine.workorder')
        self.assertEqual(action['type'], 'ir.actions.act_window')

    # ------------------------------------------------------------------
    # 7. Related / computed fields
    # ------------------------------------------------------------------
    def test_16_customer_email_related(self):
        """customer_email should reflect the partner's email."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.assertEqual(repair.customer_email, self.partner.email)

    def test_17_default_company(self):
        """company_id should default to the current company."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.assertEqual(repair.company_id, self.env.company)

    # ------------------------------------------------------------------
    # 8. Priority field
    # ------------------------------------------------------------------
    def test_18_priority_high(self):
        """Repair can be created with 'high' priority."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'priority': 'high',
        })
        self.assertEqual(repair.priority, 'high')

    def test_19_priority_low(self):
        """Repair can be created with 'low' priority."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'priority': 'low',
        })
        self.assertEqual(repair.priority, 'low')

    # ------------------------------------------------------------------
    # 9. Multiple records / batch create
    # ------------------------------------------------------------------
    def test_20_batch_create_unique_sequences(self):
        """Each record created in batch must receive a distinct repair_seq."""
        repairs = self.env['machine.repair'].create([
            {**self.repair_vals, 'name': f'Batch Repair {i}'}
            for i in range(3)
        ])
        seqs = [r.repair_seq for r in repairs]
        self.assertEqual(len(seqs), len(set(seqs)),
                         "All repair sequences must be unique.")

    # ------------------------------------------------------------------
    # 10. Warranty field
    # ------------------------------------------------------------------
    def test_21_warranty_flag(self):
        """warranty field should be stored and retrievable."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'warranty': True,
            'warranty_exp_date': date.today() + timedelta(days=365),
        })
        self.assertTrue(repair.warranty)
        self.assertIsNotNone(repair.warranty_exp_date)

    # ------------------------------------------------------------------
    # 11. is_repaired flag
    # ------------------------------------------------------------------
    def test_22_is_repaired_default_false(self):
        """is_repaired should default to False."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.assertFalse(repair.is_repaired)

    def test_23_is_repaired_can_be_set(self):
        """is_repaired can be toggled to True."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        repair.is_repaired = True
        self.assertTrue(repair.is_repaired)

    # ------------------------------------------------------------------
    # 12. Timesheet and consume part lines
    # ------------------------------------------------------------------
    def test_24_add_timesheet_line(self):
        """A timesheet line can be added to a repair."""
        repair = self.env['machine.repair'].create(dict(self.repair_vals))
        self.env['repair.timesheet'].create({
            'inverse_id': repair.id,
            'date': date.today(),
            'user_id': self.env.user.id,
            'hours': 2.5,
            'description': 'Initial inspection',
        })
        self.assertEqual(len(repair.timesheet_ids), 1)
        self.assertEqual(repair.timesheet_ids[0].hours, 2.5)

    def test_25_repair_seq_not_overwritten_on_explicit_set(self):
        """If repair_seq is explicitly provided (non-empty), it should be kept."""
        repair = self.env['machine.repair'].create({
            **self.repair_vals,
            'repair_seq': 'MANUAL-001',
        })
        self.assertEqual(repair.repair_seq, 'MANUAL-001')
