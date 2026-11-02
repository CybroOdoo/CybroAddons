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
from datetime import date
from odoo.tests.common import TransactionCase


class TestMachineConsume(TransactionCase):
    """Test cases for the MachineConsume (machine.consume) model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Consume Customer'})
        cls.today = date.today()

        # Create a product to use as a machine / spare part
        cls.product = cls.env['product.product'].create({
            'name': 'Spare Part Motor',
            'type': 'consu',
            'is_machine_parts': True,
        })
        # Create a repair to act as the consume parent
        cls.repair = cls.env['machine.repair'].create({
            'name': 'Consume Test Repair',
            'customer_id': cls.partner.id,
            'priority': 'normal',
            'repair_detail': 'Motor replacement needed.',
        })
        # Create a diagnosis to act as the consume parent
        cls.diagnosis = cls.env['machine.diagnosis'].create({
            'customer_id': cls.partner.id,
            'deadline': cls.today,
        })

    # ------------------------------------------------------------------
    # 1. Basic creation linked to repair
    # ------------------------------------------------------------------
    def test_01_create_consume_for_repair(self):
        """A machine.consume record can be created linked to a repair."""
        consume = self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
            'qty': 2.0,
        })
        self.assertTrue(consume.exists())
        self.assertEqual(consume.consume_id.id, self.repair.id)
        self.assertEqual(consume.qty, 2.0)

    def test_02_create_consume_for_diagnosis(self):
        """A machine.consume record can be created linked to a diagnosis."""
        consume = self.env['machine.consume'].create({
            'dia_estimate_id': self.diagnosis.id,
            'machine_id': self.product.id,
            'qty': 5.0,
        })
        self.assertTrue(consume.exists())
        self.assertEqual(consume.dia_estimate_id.id, self.diagnosis.id)

    # ------------------------------------------------------------------
    # 2. Quantity and duration fields
    # ------------------------------------------------------------------
    def test_03_consume_quantity_stored(self):
        """qty field value should be stored and retrievable."""
        consume = self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
            'qty': 7.5,
        })
        self.assertAlmostEqual(consume.qty, 7.5)

    def test_04_consume_hour_field(self):
        """hour (duration) field is stored correctly."""
        consume = self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
            'qty': 1.0,
            'hour': 2.25,
        })
        self.assertAlmostEqual(consume.hour, 2.25)

    def test_05_consume_default_zero_qty(self):
        """Default value for qty should be 0.0 (float default)."""
        consume = self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
        })
        self.assertAlmostEqual(consume.qty, 0.0)

    # ------------------------------------------------------------------
    # 3. Relationship via repair One2many
    # ------------------------------------------------------------------
    def test_06_consume_appears_in_repair_consume_part_ids(self):
        """A consume record linked to a repair appears in repair.consume_part_ids."""
        self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
            'qty': 3.0,
        })
        self.assertEqual(len(self.repair.consume_part_ids), 1)

    def test_07_multiple_consume_parts_for_repair(self):
        """Multiple consume parts can be added to a single repair."""
        product2 = self.env['product.product'].create({
            'name': 'Spare Part Belt',
            'type': 'consu',
            'is_machine_parts': True,
        })
        repair = self.env['machine.repair'].create({
            'name': 'Multi Part Repair',
            'customer_id': self.partner.id,
            'priority': 'high',
            'repair_detail': 'Full service.',
        })
        for p in [self.product, product2]:
            self.env['machine.consume'].create({
                'consume_id': repair.id,
                'machine_id': p.id,
                'qty': 1.0,
            })
        self.assertEqual(len(repair.consume_part_ids), 2)

    # ------------------------------------------------------------------
    # 4. Relationship via diagnosis One2many
    # ------------------------------------------------------------------
    def test_08_consume_appears_in_diagnosis_part_ids(self):
        """A consume record linked to a diagnosis appears in diagnosis.part_ids."""
        diag = self.env['machine.diagnosis'].create({
            'customer_id': self.partner.id,
            'deadline': self.today,
        })
        self.env['machine.consume'].create({
            'dia_estimate_id': diag.id,
            'machine_id': self.product.id,
            'qty': 4.0,
        })
        self.assertEqual(len(diag.part_ids), 1)
        self.assertAlmostEqual(diag.part_ids[0].qty, 4.0)

    # ------------------------------------------------------------------
    # 5. UoM field
    # ------------------------------------------------------------------
    def test_09_consume_uom_field(self):
        """uom_id field can be set on a machine.consume record."""
        uom_unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not uom_unit:
            self.skipTest("uom.product_uom_unit not available in this environment.")
        consume = self.env['machine.consume'].create({
            'consume_id': self.repair.id,
            'machine_id': self.product.id,
            'qty': 1.0,
            'uom_id': uom_unit.id,
        })
        self.assertEqual(consume.uom_id.id, uom_unit.id)

    # ------------------------------------------------------------------
    # 6. Record name (_rec_name)
    # ------------------------------------------------------------------
    def test_10_consume_rec_name_is_consume_id(self):
        """The _rec_name for machine.consume points to the consume_id field."""
        self.assertEqual(
            self.env['machine.consume']._rec_name,
            'consume_id',
            "_rec_name should be 'consume_id'."
        )
