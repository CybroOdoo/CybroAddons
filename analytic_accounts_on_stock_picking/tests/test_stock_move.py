# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from odoo.tests.common import TransactionCase, tagged


@tagged('analytic_accounts_on_stock_picking', 'stock_move')
class TestStockMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # ── Analytic ──────────────────────────────────────────────────
        cls.analytic_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not cls.analytic_plan:
            cls.analytic_plan = cls.env['account.analytic.plan'].create(
                {'name': 'Test Plan'}
            )
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Stock Test Analytic',
            'plan_id': cls.analytic_plan.id,
        })

        # ── Warehouse / locations ─────────────────────────────────────
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.loc_src = cls.warehouse.lot_stock_id
        cls.loc_dest = cls.env.ref('stock.stock_location_customers')

        # ── Product ───────────────────────────────────────────────────
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
        })

        # ── Partners ──────────────────────────────────────────────────
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.customer = cls.env['res.partner'].create({'name': 'Test Customer'})

        # ── Picking types ─────────────────────────────────────────────
        cls.picking_type_out = cls.env['stock.picking.type'].search(
            [('code', '=', 'outgoing'),
             ('warehouse_id', '=', cls.warehouse.id)],
            limit=1,
        )
        cls.picking_type_in = cls.env['stock.picking.type'].search(
            [('code', '=', 'incoming'),
             ('warehouse_id', '=', cls.warehouse.id)],
            limit=1,
        )

    # ------------------------------------------------------------------
    # Helper — 'name' removed from stock.move in Odoo 19
    # ------------------------------------------------------------------

    def _create_bare_move(self):
        """Create a stock.move with no sale/purchase line."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.loc_src.id,
            'location_dest_id': self.loc_dest.id,
        })
        move = self.env['stock.move'].create({
            'description_picking': 'Test Move',   # 'name' removed in Odoo 19
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.loc_src.id,
            'location_dest_id': self.loc_dest.id,
        })
        return move

    # ------------------------------------------------------------------
    # 1. Field existence & types
    # ------------------------------------------------------------------

    def test_analytic_field_exists(self):
        """'analytic' Json field must exist on stock.move."""
        self.assertIn('analytic', self.env['stock.move']._fields)

    def test_analytic_field_is_json(self):
        """'analytic' must be a Json field."""
        from odoo.fields import Json
        self.assertIsInstance(self.env['stock.move']._fields['analytic'], Json)

    def test_analytic_precision_field_exists(self):
        """'analytic_precision' Integer field must exist on stock.move."""
        self.assertIn('analytic_precision', self.env['stock.move']._fields)

    def test_analytic_precision_field_is_integer(self):
        """'analytic_precision' must be an Integer field."""
        from odoo.fields import Integer
        self.assertIsInstance(
            self.env['stock.move']._fields['analytic_precision'], Integer
        )

    # ------------------------------------------------------------------
    # 2. analytic_precision default
    # ------------------------------------------------------------------

    def test_analytic_precision_default_matches_decimal_precision(self):
        """analytic_precision must equal the 'Percentage Analytic' dp value."""
        expected = self.env['decimal.precision'].precision_get('Percentage Analytic')
        move = self._create_bare_move()
        self.assertEqual(move.analytic_precision, expected)

    # ------------------------------------------------------------------
    # 3. Bare move → analytic is False
    # ------------------------------------------------------------------

    def test_analytic_false_on_bare_move(self):
        """A move with no sale/purchase line must have analytic = False."""
        move = self._create_bare_move()
        self.assertFalse(move.analytic)

    # ------------------------------------------------------------------
    # 4. Move linked to sale.order.line → analytic is False (by design)
    # ------------------------------------------------------------------

    def test_analytic_false_when_sale_line_set(self):
        """Sale-side moves return analytic = False regardless of distribution."""
        # Odoo 19: pricelist_id is optional on sale.order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'analytic_distribution': {str(self.analytic_account.id): 100},
            })],
        })
        sale_line = sale_order.order_line[:1]

        move = self._create_bare_move()
        move.sale_line_id = sale_line
        move.invalidate_recordset(['analytic'])

        self.assertFalse(
            move.analytic,
            "analytic must be False when sale_line_id is set (by design)",
        )

    # ------------------------------------------------------------------
    # 5. Move linked to purchase.order.line WITH analytic_distribution
    # ------------------------------------------------------------------

    def test_analytic_equals_purchase_line_distribution(self):
        """analytic must equal purchase_line_id.analytic_distribution."""
        distribution = {str(self.analytic_account.id): 100}

        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 50.0,
                'date_planned': '2026-01-01',
                'analytic_distribution': distribution,
            })],
        })
        purchase_line = po.order_line[:1]

        move = self._create_bare_move()
        move.purchase_line_id = purchase_line
        move.invalidate_recordset(['analytic'])

        self.assertEqual(move.analytic, distribution)

    # ------------------------------------------------------------------
    # 6. Move linked to purchase.order.line WITHOUT analytic_distribution
    # ------------------------------------------------------------------

    def test_analytic_false_when_purchase_line_has_no_distribution(self):
        """analytic must be False when purchase_line has no distribution."""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 50.0,
                'date_planned': '2026-01-01',
            })],
        })
        purchase_line = po.order_line[:1]

        move = self._create_bare_move()
        move.purchase_line_id = purchase_line
        move.invalidate_recordset(['analytic'])

        self.assertFalse(move.analytic)

    # ------------------------------------------------------------------
    # 7. Recomputation after purchase_line_id change
    # ------------------------------------------------------------------

    def test_analytic_recomputes_when_purchase_line_changes(self):
        """Swapping purchase_line_id re-triggers _compute_analytic."""
        distribution = {str(self.analytic_account.id): 100}

        po1 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 10.0,
                'date_planned': '2026-01-01',
            })],
        })
        po2 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 10.0,
                'date_planned': '2026-01-01',
                'analytic_distribution': distribution,
            })],
        })

        move = self._create_bare_move()

        move.purchase_line_id = po1.order_line[:1]
        move.invalidate_recordset(['analytic'])
        self.assertFalse(move.analytic)

        move.purchase_line_id = po2.order_line[:1]
        move.invalidate_recordset(['analytic'])
        self.assertEqual(move.analytic, distribution)