# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo.tests import tagged

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestQualityMeasure(QualityCommon):

    def test_default_values(self):
        measure = self.env['quality.measure'].create({'name': 'Defaults'})
        self.assertEqual(measure.type, 'quantity')
        self.assertTrue(measure.active)
        self.assertEqual(measure.company_id, self.env.company)

    def test_product_template_related(self):
        self.assertEqual(self.measure_qty.product_template_id,
                         self.product.product_tmpl_id)

    def test_onchange_type_quality_resets_quantities(self):
        measure = self.env['quality.measure'].new({
            'name': 'Onchange',
            'type': 'quality',
            'quantity_min': 3.0,
            'quantity_max': 8.0,
        })
        measure.onchange_type()
        self.assertEqual(measure.quantity_min, 0.0)
        self.assertEqual(measure.quantity_max, 0.0)

    def test_onchange_type_quantity_keeps_quantities(self):
        measure = self.env['quality.measure'].new({
            'name': 'Onchange',
            'type': 'quantity',
            'quantity_min': 3.0,
            'quantity_max': 8.0,
        })
        measure.onchange_type()
        self.assertEqual(measure.quantity_min, 3.0)
        self.assertEqual(measure.quantity_max, 8.0)

    def test_toggle_active(self):
        self.assertTrue(self.measure_qty.active)
        self.measure_qty.toggle_active()
        self.assertFalse(self.measure_qty.active)
        self.measure_qty.toggle_active()
        self.assertTrue(self.measure_qty.active)

    def test_archived_measure_hidden_from_default_search(self):
        self.measure_qty.toggle_active()
        found = self.env['quality.measure'].search(
            [('id', '=', self.measure_qty.id)])
        self.assertFalse(found)

    def test_product_deletion_cascades_to_measure(self):
        product = self.env['product.product'].create(
            {'name': 'Temp Product', 'type': 'consu'})
        measure = self.env['quality.measure'].create(
            {'name': 'Temp Measure', 'product_id': product.id})
        product.unlink()
        self.assertFalse(measure.exists())
