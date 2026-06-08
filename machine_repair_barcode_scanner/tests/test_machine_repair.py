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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestMachineRepair(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.customer = cls.env['res.partner'].create({
            'name': 'Demo Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Demo Machine',
            'barcode': '2112345678901',
        })

        cls.repair_order = cls.env['machine.repair'].create({
            'name': 'Repair Order',
            'repair_seq': 'MRP/001',
            'customer_id': cls.customer.id,
            'priority': 'low',
            'repair_detail': 'Test repair detail',
        })

    def test_barcode_search_machine(self):
        """Test barcode search for machine."""

        result = self.env['machine.repair'].barcode_search([
            '2112345678901',
            self.repair_order.id,
            'machine'
        ])

        self.assertTrue(result)

        self.assertEqual(
            self.repair_order.machine_id,
            self.product
        )

    def test_barcode_search_invalid(self):
        """Test invalid barcode."""

        result = self.env['machine.repair'].barcode_search([
            '0000000000000',
            self.repair_order.id,
            'machine'
        ])

        self.assertFalse(result)