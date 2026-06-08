# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestMrpUnbuildStandalone(TransactionCase):
    """Test coverage for custom logic in mrp.unbuild (mrp_standalone_unbuild)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.location_stock = cls.env.ref("stock.stock_location_stock")

        cls.finished_product = cls.env["product.product"].create(
            {
                "name": "Test Finished Product (Unbuild)",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.component_1 = cls.env["product.product"].create(
            {
                "name": "Test Component 1 (Unbuild)",
                "is_storable": True,
                "tracking": "none",
            }
        )
        cls.component_2 = cls.env["product.product"].create(
            {
                "name": "Test Component 2 (Unbuild)",
                "is_storable": True,
                "tracking": "none",
            }
        )

        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "product_uom_id": cls.uom_unit.id,
                "type": "normal",
                "company_id": cls.company.id,
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.component_1.id, "product_qty": 2.0, "product_uom_id": cls.uom_unit.id}),
                    (0, 0, {"product_id": cls.component_2.id, "product_qty": 3.0, "product_uom_id": cls.uom_unit.id}),
                ],
            }
        )

        # Lots for allowed lot computation + tracking check in action_unbuild
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "LOT-UNBUILD-1", "product_id": cls.finished_product.id, "company_id": cls.company.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "LOT-UNBUILD-2", "product_id": cls.finished_product.id, "company_id": cls.company.id}
        )

        # Make finished product available in stock with a lot.
        cls.env["stock.quant"]._update_available_quantity(
            cls.finished_product.with_company(cls.company),
            cls.location_stock,
            5.0,
            lot_id=cls.lot_1,
        )

    def _new_unbuild(self, qty=1.0, lot=None):
        return self.env["mrp.unbuild"].create(
            {
                "product_id": self.finished_product.id,
                "product_qty": qty,
                "bom_id": self.bom.id,
                "company_id": self.company.id,
                "location_id": self.location_stock.id,
                "location_dest_id": self.location_stock.id,
                "lot_id": lot.id if lot else False,
            }
        )

    def test_compute_allowed_lot_ids_without_mo(self):
        unbuild = self._new_unbuild(qty=1.0, lot=self.lot_1)
        unbuild.mo_id = False
        unbuild._compute_allowed_lot_ids()

        self.assertIn(self.lot_1, unbuild.allowed_lot_ids)
        self.assertIn(self.lot_2, unbuild.allowed_lot_ids)

    def test_onchange_bom_id_populates_unbuild_lines(self):
        unbuild = self._new_unbuild(qty=2.0, lot=self.lot_1)
        unbuild._onchange_bom_id_populate_lines()

        self.assertTrue(unbuild.unbuild_line_ids, "BoM onchange should populate unbuild_line_ids")
        self.assertEqual(set(unbuild.unbuild_line_ids.mapped("product_id").ids), {self.component_1.id, self.component_2.id})

        line_1 = unbuild.unbuild_line_ids.filtered(lambda l: l.product_id == self.component_1)
        line_2 = unbuild.unbuild_line_ids.filtered(lambda l: l.product_id == self.component_2)
        self.assertEqual(len(line_1), 1)
        self.assertEqual(len(line_2), 1)
        self.assertAlmostEqual(line_1.qty, 4.0, places=6)
        self.assertAlmostEqual(line_2.qty, 6.0, places=6)

    def test_generate_consume_moves_without_mo_uses_finished_product(self):
        unbuild = self._new_unbuild(qty=1.0, lot=self.lot_1)
        unbuild._onchange_bom_id_populate_lines()
        unbuild.mo_id = False

        consume_moves = unbuild._generate_consume_moves()
        self.assertEqual(len(consume_moves), 1)
        self.assertEqual(consume_moves.product_id, self.finished_product)
        self.assertEqual(consume_moves.product_uom_qty, 1.0)

    def test_generate_produce_moves_without_mo_uses_custom_lines(self):
        unbuild = self._new_unbuild(qty=1.0, lot=self.lot_1)
        unbuild._onchange_bom_id_populate_lines()
        unbuild.mo_id = False

        produced_moves = unbuild._generate_produce_moves()
        self.assertTrue(produced_moves)

        by_product = {m.product_id.id: m.product_uom_qty for m in produced_moves}
        self.assertAlmostEqual(by_product.get(self.component_1.id, 0.0), 2.0, places=6)
        self.assertAlmostEqual(by_product.get(self.component_2.id, 0.0), 3.0, places=6)

    def test_action_unbuild_without_mo_completes_and_creates_moves(self):
        unbuild = self._new_unbuild(qty=1.0, lot=self.lot_1)
        unbuild._onchange_bom_id_populate_lines()
        unbuild.mo_id = False

        unbuild.action_unbuild()
        self.assertEqual(unbuild.state, "done")
        self.assertTrue(unbuild.produce_line_ids)

        # In the current standalone implementation, consume moves are also
        # linked through `unbuild_id`, so they end up in `produce_line_ids`
        # rather than `consume_line_ids`.
        move_products = set(unbuild.produce_line_ids.mapped("product_id").ids)
        self.assertIn(self.finished_product.id, move_products)
        self.assertIn(self.component_1.id, move_products)
        self.assertIn(self.component_2.id, move_products)
