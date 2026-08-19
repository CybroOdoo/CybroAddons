# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestQualityMeasure(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product QM',
        })

    def test_01_onchange_type(self):
        """Test onchange_type resets quantity_min and quantity_max."""
        measure = self.env['quality.measure'].new({
            'name': 'Test Measure',
            'product_id': self.product.id,
            'type': 'quantity',
            'quantity_min': 10.0,
            'quantity_max': 20.0,
        })
        
        # Trigger onchange
        measure.type = 'quality'
        measure.onchange_type()
        
        self.assertEqual(measure.quantity_min, 0.0, "quantity_min should reset to 0.0")
        self.assertEqual(measure.quantity_max, 0.0, "quantity_max should reset to 0.0")
