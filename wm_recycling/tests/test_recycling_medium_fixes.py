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
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_recycling')
class TestRecyclingMediumFixes(TransactionCase):
    """Regression tests: per-line source material, one active order per
    batch and company-scoped scrap/production locations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Medium Fix WH',
            'code': 'MFWH',
        })
        cls.location = cls.warehouse.lot_stock_id
        product_vals = {
            'is_waste_material': True,
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.uom_unit.id,
        }
        cls.material_a = cls.env['product.product'].create(dict(product_vals, name='MF PET Waste'))
        cls.material_b = cls.env['product.product'].create(dict(product_vals, name='MF Alu Waste'))
        cls.output_a = cls.env['product.product'].create({
            'name': 'MF PET Flakes', 'type': 'consu', 'is_storable': True, 'uom_id': cls.uom_unit.id,
        })
        cls.output_b = cls.env['product.product'].create({
            'name': 'MF Alu Ingot', 'type': 'consu', 'is_storable': True, 'uom_id': cls.uom_unit.id,
        })
        SortConfig = cls.env['wm.waste.material.sort.config']
        for material, output in ((cls.material_a, cls.output_a), (cls.material_b, cls.output_b)):
            SortConfig.create({
                'material_id': material.product_tmpl_id.id,
                'dest_product_id': output.id,
                'dest_location_id': cls.location.id,
            })
        cls.batch = cls.env['waste.batch'].create({
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.location.id,
            'line_ids': [
                (0, 0, {'product_id': cls.material_a.id, 'quantity': 50.0}),
                (0, 0, {'product_id': cls.material_b.id, 'quantity': 30.0}),
            ],
        })

    def test_onchange_lines_consume_their_own_material(self):
        """R-02: each generated recovery line consumes its own batch material."""
        order = self.env['recycling.order'].new({'waste_batch_id': self.batch.id})
        order._onchange_waste_batch_pre_fill_material()
        by_output = {line.product_id: line.source_product_id for line in order.line_ids}
        self.assertEqual(by_output[self.output_a], self.material_a)
        self.assertEqual(by_output[self.output_b], self.material_b)

    def test_single_active_order_per_batch(self):
        """R-03: only one non-cancelled recycling order per waste batch."""
        first = self.env['recycling.order'].create({'waste_batch_id': self.batch.id})
        with self.assertRaises(ValidationError):
            self.env['recycling.order'].create({'waste_batch_id': self.batch.id})
        first.action_cancel()
        second = self.env['recycling.order'].create({'waste_batch_id': self.batch.id})
        # The cancelled one cannot come back while another order is active
        with self.assertRaises(ValidationError):
            first.action_reset_draft()
        self.assertEqual(second.state, 'draft')

    def test_scrap_location_is_company_scrap_not_inventory_adjustment(self):
        """R-04: process loss goes to the dedicated per-company
        "Recycling Process Loss" location, not inventory adjustment."""
        order = self.env['recycling.order'].create({'waste_batch_id': self.batch.id})
        scrap = order._get_scrap_location()
        self.assertTrue(scrap)
        self.assertEqual(scrap.name, 'Recycling Process Loss')
        self.assertEqual(scrap.usage, 'inventory')
        self.assertEqual(scrap.company_id, order.company_id)
        inventory_loss = self.env['ir.default'].sudo()._get(
            'product.template', 'property_stock_inventory', company_id=order.company_id.id)
        self.assertNotEqual(scrap.id, inventory_loss)

    def test_recovery_moves_use_order_company_production_location(self):
        """R-04: stock moves use the order company and its production location."""
        order = self.env['recycling.order'].create({
            'waste_batch_id': self.batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.output_b.id,
                'uom_id': self.uom_unit.id,
                'source_product_id': self.material_b.id,
                'dest_location_id': self.location.id,
                'recovered_qty': 10.0,
            })],
        })
        line = order.line_ids
        line._move_recovered_stock()
        self.assertTrue(line.is_stocked)
        for move in (line.stock_move_id, line.consumption_move_id):
            self.assertEqual(move.company_id, order.company_id)
        production = line.stock_move_id.location_id
        self.assertEqual(production.usage, 'production')
        self.assertIn(production.company_id, (order.company_id, self.env['res.company']))
        # Consumption takes the line's own source material
        self.assertEqual(line.consumption_move_id.product_id, self.material_b)
