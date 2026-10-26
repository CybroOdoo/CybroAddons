#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_recycling')
class TestRecyclingLowFixes(TransactionCase):
    """L-15: grouped landfill diversion is total recycled / total intake,
    not an average of per-line shares."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.warehouse = cls.env['stock.warehouse'].create({'name': 'Low Fix WH', 'code': 'LFWH'})
        cls.location = cls.warehouse.lot_stock_id
        cls.material = cls.env['product.product'].create({
            'name': 'LF PET Waste', 'is_waste_material': True, 'type': 'consu',
            'is_storable': True, 'uom_id': uom_unit.id,
        })
        cls.output = cls.env['product.product'].create({
            'name': 'LF PET Flakes', 'type': 'consu', 'is_storable': True, 'uom_id': uom_unit.id,
        })
        cls.uom_unit = uom_unit

    def _order(self, input_qty, recovered):
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {'product_id': self.material.id, 'quantity': input_qty})],
        })
        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.output.id,
                'uom_id': self.uom_unit.id,
                'source_product_id': self.material.id,
                'dest_location_id': self.location.id,
                'recovered_qty': qty,
            }) for qty in recovered],
        })
        self.env.flush_all()
        # Bypass the processing workflow: only the reported figures matter here
        self.env.cr.execute(
            "UPDATE recycling_order SET state = 'in_progress', input_qty = %s WHERE id = %s",
            (input_qty, order.id))
        self.env.invalidate_all()
        return order

    def test_grouped_diversion_is_weighted(self):
        order_1 = self._order(100.0, [30.0, 30.0])   # 60 %
        order_2 = self._order(100.0, [10.0])         # 10 %
        line_ids = (order_1.line_ids | order_2.line_ids).ids
        Report = self.env['wm.carbon.accounting.report']
        rows = Report.search([('id', 'in', line_ids)])
        self.assertEqual(len(rows), 3)
        self.assertAlmostEqual(sum(rows.mapped('input_qty_kg')), 200.0)

        [(input_sum, recycled_sum, pct)] = Report._read_group(
            [('id', 'in', line_ids)], [],
            ['input_qty_kg:sum', 'recycled_qty_kg:sum', 'landfill_diversion_pct:avg'])
        self.assertAlmostEqual(input_sum, 200.0)
        self.assertAlmostEqual(recycled_sum, 70.0)
        # Plain average of the row shares would give (30 + 30 + 10) / 3
        self.assertAlmostEqual(pct, 35.0)

        groups = Report.formatted_read_group(
            [('id', 'in', line_ids)], ['source_product_id'], ['landfill_diversion_pct:avg'])
        self.assertAlmostEqual(groups[0]['landfill_diversion_pct:avg'], 35.0)

    def test_reports_convert_units_to_kg(self):
        """Carbon and efficiency reports express weights in kg and give the
        same CO2 as the order lines, whatever unit the line is entered in."""
        kg = self.env.ref('uom.product_uom_kgm')
        ton = self.env.ref('uom.product_uom_ton')
        cat = self.env['wm.waste.category'].create(
            {'name': 'Report Unit Cat', 'code': 'RUC', 'warm_factor_co2': 2.0})
        material = self.env['product.product'].create({
            'name': 'RU Waste', 'is_waste_material': True, 'type': 'consu',
            'is_storable': True, 'uom_id': kg.id, 'wm_waste_category_id': cat.id,
        })
        output = self.env['product.product'].create({
            'name': 'RU Out', 'type': 'consu', 'is_storable': True, 'uom_id': ton.id,
        })
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {'product_id': material.id, 'quantity': 2000.0, 'uom_id': kg.id})],
        })
        order = self.env['recycling.order'].create({
            'waste_batch_id': batch.id,
            'line_ids': [(0, 0, {
                'product_id': output.id, 'uom_id': ton.id,
                'source_product_id': material.id,
                'dest_location_id': self.location.id,
                'expected_qty': 1.0, 'recovered_qty': 1.0,
            })],
        })
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE recycling_order SET state = 'done' WHERE id = %s", (order.id,))
        self.env.invalidate_all()
        self.assertAlmostEqual(order.co2_avoided_tons, 2.0)
        carbon = self.env['wm.carbon.accounting.report'].search([('id', 'in', order.line_ids.ids)])
        self.assertAlmostEqual(carbon.recycled_qty_kg, 1000.0)
        self.assertAlmostEqual(carbon.input_qty_kg, 2000.0)
        self.assertAlmostEqual(carbon.co2_avoided_tons, 2.0)
        self.assertAlmostEqual(carbon.landfill_diversion_pct, 50.0)
        eff = self.env['wm.recycling.efficiency.report'].search([('id', 'in', order.line_ids.ids)])
        self.assertAlmostEqual(eff.actual_qty, 1000.0)
        self.assertAlmostEqual(eff.target_qty, 1000.0)
        self.assertAlmostEqual(eff.co2_avoided_tons, 2.0)
        self.assertAlmostEqual(eff.efficiency_pct, 100.0)
