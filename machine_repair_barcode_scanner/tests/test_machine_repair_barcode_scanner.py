# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMachineRepairBarcodeScanner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.machine_product = cls.env['product.product'].create({
            'name': 'Test Machine',
            'type': 'consu',
            'is_machine': True,
        })
        cls.part_product = cls.env['product.product'].create({
            'name': 'Test Part',
            'type': 'consu',
            'is_machine_parts': True,
        })
        cls.machine_product.action_generate_barcode()
        cls.part_product.action_generate_barcode()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Customer',
        })
        cls.repair_order = cls.env['machine.repair'].create({
            'name': 'Test Repair',
            'customer_id': cls.partner.id,
            'priority': 'low',
            'closing_date': fields.Date.today(),
            'repair_detail': 'Test repair detail',
        })

    def test_barcode_generation(self):
        """Test barcode generated for product."""
        self.assertTrue(
            self.machine_product.barcode
        )
        self.assertEqual(
            len(self.machine_product.barcode),
            13
        )

    def test_barcode_search_machine(self):
        """Test machine assignment from barcode."""
        result = self.env['machine.repair'].barcode_search([
            self.machine_product.barcode,
            self.repair_order.id,
            'machine'
        ])
        self.assertTrue(result)
        self.assertEqual(
            self.repair_order.machine_id,
            self.machine_product
        )

    def test_barcode_search_consumable(self):
        """Test consumable part addition."""
        result = self.env['machine.repair'].barcode_search([
            self.part_product.barcode,
            self.repair_order.id,
            'part'
        ])
        self.assertTrue(result)
        consume_part = self.repair_order.consume_part_ids.filtered(
            lambda rec: rec.machine_id == self.part_product
        )
        self.assertTrue(consume_part)
        self.assertEqual(
            consume_part.qty,
            1
        )

    def test_barcode_search_increment_qty(self):
        """Test consumable quantity increment."""
        self.env['machine.repair'].barcode_search([
            self.part_product.barcode,
            self.repair_order.id,
            'part'
        ])
        self.env['machine.repair'].barcode_search([
            self.part_product.barcode,
            self.repair_order.id,
            'part'
        ])
        consume_part = self.repair_order.consume_part_ids.filtered(
            lambda rec: rec.machine_id == self.part_product
        )
        self.assertEqual(
            consume_part.qty,
            2
        )

    def test_invalid_barcode(self):
        """Test invalid barcode returns False."""
        result = self.env['machine.repair'].barcode_search([
            'INVALID_BARCODE',
            self.repair_order.id,
            'machine'
        ])
        self.assertFalse(result)
