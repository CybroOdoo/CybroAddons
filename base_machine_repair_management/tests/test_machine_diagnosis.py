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
from odoo.tools import mute_logger


class TestMachineDiagnosis(TransactionCase):
    """Test cases for the MachineDiagnosis model (machine.diagnosis)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Diagnosis Customer',
            'email': 'diag@example.com',
        })
        cls.today = date.today()
        cls.deadline = cls.today + timedelta(days=10)
        cls.diagnosis_vals = {
            'customer_id': cls.partner.id,
            'deadline': cls.deadline,
        }

    # ------------------------------------------------------------------
    # 1. Creation & sequence
    # ------------------------------------------------------------------
    def test_01_create_diagnosis_sequence_generated(self):
        """A new diagnosis record should receive a sequence number."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        self.assertNotEqual(diag.diagnosis_seq, 'New',
                            "diagnosis_seq must be set by sequence on create.")
        self.assertTrue(diag.diagnosis_seq)

    def test_02_create_diagnosis_required_customer(self):
        """Creating a diagnosis without a customer should raise."""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['machine.diagnosis'].create({
                'deadline': self.deadline,
                # customer_id is missing — required
            })

    def test_03_create_diagnosis_required_deadline(self):
        """Creating a diagnosis without a deadline should raise."""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['machine.diagnosis'].create({
                'customer_id': self.partner.id,
                # deadline is missing — required
            })

    # ------------------------------------------------------------------
    # 2. Batch create — unique sequences
    # ------------------------------------------------------------------
    def test_04_batch_create_unique_sequences(self):
        """Each diagnosis in a batch must receive a distinct sequence."""
        diagnoses = self.env['machine.diagnosis'].create([
            {**self.diagnosis_vals} for _ in range(3)
        ])
        seqs = [d.diagnosis_seq for d in diagnoses]
        self.assertEqual(len(seqs), len(set(seqs)),
                         "All diagnosis sequences must be unique.")

    # ------------------------------------------------------------------
    # 3. Relationship to machine.repair
    # ------------------------------------------------------------------
    def test_05_diagnosis_linked_to_repair(self):
        """A diagnosis created from a repair should reference that repair."""
        repair = self.env['machine.repair'].create({
            'name': 'Repair for Diag Link',
            'customer_id': self.partner.id,
            'priority': 'normal',
            'repair_detail': 'Check motor.',
            'repair_req_date': self.today,
            'closing_date': self.deadline,
        })
        result = repair.action_create_diagnosis()
        diag = self.env['machine.diagnosis'].browse(result['res_id'])
        self.assertEqual(diag.machine_repair_ref_id.id, repair.id)

    # ------------------------------------------------------------------
    # 4. action_create_quotation
    # ------------------------------------------------------------------
    def test_06_create_quotation_without_parts(self):
        """action_create_quotation() creates a sale.order with no lines when parts are empty."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        result = diag.action_create_quotation()
        self.assertEqual(result['res_model'], 'sale.order')
        quotation = self.env['sale.order'].browse(result['res_id'])
        self.assertTrue(quotation.exists())
        self.assertEqual(quotation.partner_id.id, self.partner.id)

    def test_07_quotation_machine_diagnosis_ref(self):
        """The created sale.order should carry the diagnosis sequence reference."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        result = diag.action_create_quotation()
        quotation = self.env['sale.order'].browse(result['res_id'])
        self.assertEqual(quotation.machine_diagnosis_ref, diag.diagnosis_seq)

    def test_08_quotation_date_is_deadline(self):
        """The sale.order date_order should match the diagnosis deadline."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        result = diag.action_create_quotation()
        quotation = self.env['sale.order'].browse(result['res_id'])
        # date_order is a Datetime but deadline is a Date — compare date part
        self.assertEqual(quotation.date_order.date(), self.deadline)

    # ------------------------------------------------------------------
    # 5. Part lines relationship
    # ------------------------------------------------------------------
    def test_09_add_part_to_diagnosis(self):
        """A machine.consume record can be linked to a diagnosis."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        product = self.env['product.product'].create({
            'name': 'Spare Part A',
            'type': 'consu',
            'is_machine_parts': True,
        })
        consume = self.env['machine.consume'].create({
            'dia_estimate_id': diag.id,
            'machine_id': product.id,
            'qty': 3.0,
        })
        self.assertEqual(len(diag.part_ids), 1)
        self.assertEqual(diag.part_ids[0].qty, 3.0)
        self.assertEqual(consume.dia_estimate_id.id, diag.id)

    # ------------------------------------------------------------------
    # 6. Timesheet lines
    # ------------------------------------------------------------------
    def test_10_add_timesheet_to_diagnosis(self):
        """A repair.timesheet record can be linked to a diagnosis."""
        diag = self.env['machine.diagnosis'].create(dict(self.diagnosis_vals))
        self.env['repair.timesheet'].create({
            'diagnosis_id': diag.id,
            'date': self.today,
            'user_id': self.env.user.id,
            'hours': 1.5,
            'description': 'Diagnosis check',
        })
        self.assertEqual(len(diag.timesheet_ids), 1)
        self.assertEqual(diag.timesheet_ids[0].hours, 1.5)

    # ------------------------------------------------------------------
    # 7. Field defaults
    # ------------------------------------------------------------------
    def test_11_diagnosis_seq_default_new(self):
        """Before the create override runs, diagnosis_seq defaults to 'New'."""
        # We access the field default via the model's _fields
        field = self.env['machine.diagnosis']._fields['diagnosis_seq']
        default_val = field.default(self.env['machine.diagnosis'])
        self.assertEqual(default_val, 'New')

    def test_12_assigning_date_field_stored(self):
        """assigning_date can be stored and retrieved correctly."""
        diag = self.env['machine.diagnosis'].create({
            **self.diagnosis_vals,
            'assigning_date': self.today,
        })
        self.assertEqual(diag.assigning_date, self.today)
