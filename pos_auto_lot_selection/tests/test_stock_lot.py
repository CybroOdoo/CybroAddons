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

from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockLotAutoSelection(TransactionCase):
    """Tests for get_available_lots_for_pos on stock.lot."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id

        cls.pos_config = cls.env['pos.config'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        if not cls.pos_config:
            picking_type = cls.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('warehouse_id', '=', cls.warehouse.id),
            ], limit=1)
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS',
                'picking_type_id': picking_type.id,
            })
        if cls.pos_config.picking_type_id:
            cls.pos_config.picking_type_id.default_location_src_id = cls.stock_location

        cls.categ = cls.env['product.category'].create({'name': 'Test Cat'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'tracking': 'lot',
            'categ_id': cls.categ.id,
        })

        removal_lifo = cls.env['product.removal'].search(
            [('method', '=', 'lifo')], limit=1)
        cls.categ_lifo = cls.env['product.category'].create({
            'name': 'LIFO Cat',
            'removal_strategy_id': removal_lifo.id if removal_lifo else False,
        })
        cls.product_lifo = cls.env['product.product'].create({
            'name': 'LIFO Product',
            'type': 'product',
            'tracking': 'lot',
            'categ_id': cls.categ_lifo.id,
        })

        cls.Lot = cls.env['stock.lot']

    def _make_lot(self, product, name, qty, **kw):
        """Create a lot + quant in one call."""
        lot = self.Lot.create({
            'name': name,
            'product_id': product.id,
            'company_id': self.company.id,
            **{k: v for k, v in kw.items() if k in ('is_taken',)},
        })
        self.env['stock.quant'].sudo().create({
            'product_id': product.id,
            'lot_id': lot.id,
            'quantity': qty,
            'reserved_quantity': kw.get('reserved', 0),
            'location_id': self.stock_location.id,
            'company_id': self.company.id,
            **(({'in_date': kw['in_date']} if 'in_date' in kw else {})),
        })
        return lot

    # -- Core happy path --
    def test_single_lot(self):
        """Basic: returns correct lot names for requested qty."""
        self._make_lot(self.product, 'LOT-1', 5)
        result = self.Lot.get_available_lots_for_pos(self.product.id, 3)
        self.assertEqual(result, ['LOT-1'] * 3)

    # -- Edge cases returning False --
    def test_nonexistent_product(self):
        """Non-existent product returns False."""
        self.assertFalse(
            self.Lot.get_available_lots_for_pos(999999999, 1))

    def test_no_stock(self):
        """No lots/quants → False."""
        self.assertFalse(
            self.Lot.get_available_lots_for_pos(self.product.id, 1))

    # -- is_taken filtering --
    def test_is_taken_excluded(self):
        """Lots with is_taken=True are skipped."""
        self._make_lot(self.product, 'TAKEN', 5, is_taken=True)
        self._make_lot(self.product, 'AVAIL', 5)
        result = self.Lot.get_available_lots_for_pos(self.product.id, 2)
        self.assertEqual(result, ['AVAIL'] * 2)

    # -- Reserved qty --
    def test_reserved_deducted(self):
        """Fully reserved lot is skipped; partial reservation reduces qty."""
        self._make_lot(self.product, 'FULL-RES', 5, reserved=5)
        self._make_lot(self.product, 'PART-RES', 5, reserved=3)
        result = self.Lot.get_available_lots_for_pos(self.product.id, 2)
        self.assertEqual(result, ['PART-RES'] * 2)

    # -- FIFO ordering --
    def test_fifo_order(self):
        """Default FIFO: older lot consumed first."""
        now = datetime.now()
        self._make_lot(self.product, 'OLD', 2, in_date=now - timedelta(days=10))
        self._make_lot(self.product, 'NEW', 2, in_date=now)
        result = self.Lot.get_available_lots_for_pos(self.product.id, 3)
        self.assertEqual(result[:2], ['OLD', 'OLD'])
        self.assertEqual(result[2], 'NEW')

    # -- LIFO ordering --
    def test_lifo_order(self):
        """LIFO: newer lot consumed first."""
        now = datetime.now()
        self._make_lot(self.product_lifo, 'OLD', 2, in_date=now - timedelta(days=10))
        self._make_lot(self.product_lifo, 'NEW', 2, in_date=now)
        result = self.Lot.get_available_lots_for_pos(self.product_lifo.id, 3)
        self.assertEqual(result[:2], ['NEW', 'NEW'])
        self.assertEqual(result[2], 'OLD')

    # -- Assigned lots deduction --
    def test_assigned_lots_deducted(self):
        """Already-assigned lots in POS session reduce availability."""
        self._make_lot(self.product, 'LOT-A', 5)
        result = self.Lot.get_available_lots_for_pos(
            self.product.id, 2, fetched_assigned_lots=['LOT-A'] * 3)
        self.assertEqual(result, ['LOT-A'] * 2)

    # -- Insufficient stock --
    def test_partial_fulfillment(self):
        """Returns whatever is available when stock < requested qty."""
        self._make_lot(self.product, 'SHORT', 2)
        result = self.Lot.get_available_lots_for_pos(self.product.id, 5)
        self.assertEqual(result, ['SHORT'] * 2)

    # -- is_taken field default --
    def test_is_taken_default(self):
        """is_taken defaults to False."""
        lot = self._make_lot(self.product, 'DFLT', 1)
        self.assertFalse(lot.is_taken)
