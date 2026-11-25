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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestBarcodeManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.model = cls.env['barcode.management']

        # Setup locations
        cls.loc_stock = cls.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not cls.loc_stock:
            cls.loc_stock = cls.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not cls.loc_stock:
            cls.loc_stock = cls.env['stock.location'].create({'name': 'Stock', 'usage': 'internal'})

        cls.loc_customers = cls.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not cls.loc_customers:
            cls.loc_customers = cls.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
        if not cls.loc_customers:
            cls.loc_customers = cls.env['stock.location'].create({'name': 'Customers', 'usage': 'customer'})

        cls.loc_suppliers = cls.env.ref('stock.stock_location_suppliers', raise_if_not_found=False)
        if not cls.loc_suppliers:
            cls.loc_suppliers = cls.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
        if not cls.loc_suppliers:
            cls.loc_suppliers = cls.env['stock.location'].create({'name': 'Suppliers', 'usage': 'supplier'})

        # Setup picking types
        cls.picking_type_out = cls.env.ref('stock.picking_type_out', raise_if_not_found=False)
        if not cls.picking_type_out:
            cls.picking_type_out = cls.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)

        cls.picking_type_in = cls.env.ref('stock.picking_type_in', raise_if_not_found=False)
        if not cls.picking_type_in:
            cls.picking_type_in = cls.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)

        cls.picking_type_internal = cls.env.ref('stock.picking_type_internal', raise_if_not_found=False)
        if not cls.picking_type_internal:
            cls.picking_type_internal = cls.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        # Setup products
        cls.product_untracked = cls.env['product.product'].create({
            'name': 'Untracked Barcode Product',
            'type': 'consu',
            'is_storable': True,
            'barcode': 'PROD_UNTRACKED_01',
            'tracking': 'none',
        })
        cls.product_serial = cls.env['product.product'].create({
            'name': 'Serial Barcode Product',
            'type': 'consu',
            'is_storable': True,
            'barcode': 'PROD_SERIAL_01',
            'tracking': 'serial',
        })
        cls.product_lot = cls.env['product.product'].create({
            'name': 'Lot Barcode Product',
            'type': 'consu',
            'is_storable': True,
            'barcode': 'PROD_LOT_01',
            'tracking': 'lot',
        })

    def _create_test_picking(self, picking_type, location_id, location_dest_id, with_barcode=True):
        return self.env['stock.picking'].create({
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'with_barcode': with_barcode,
        })

    def test_return_barcode_models(self):
        """Test that barcode models are correctly returned based on user rights"""
        models = self.model.return_barcode_models()
        self.assertIsInstance(models, dict)
        self.assertIn('product.product', models)
        self.assertIn('stock.picking', models)

    def test_search_barcode_in_models(self):
        """Test searching barcodes across specified models (found & not found)"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        # 1. Product found
        res_found = self.model.search_barcode_in_models('PROD_UNTRACKED_01', picking.id)
        self.assertFalse(res_found['is_error'])
        self.assertEqual(res_found['res_model'], 'product.product')

        # 2. Barcode not found
        res_missing = self.model.search_barcode_in_models('NON_EXISTENT_BARCODE_XYZ', picking.id)
        self.assertTrue(res_missing['is_error'])

        # 3. With batch_id
        batch = self.env['stock.picking.batch'].create({'name': 'Batch Search Test'})
        res_batch = self.model.search_barcode_in_models('PROD_UNTRACKED_01', picking.id, batch_id=batch.id)
        self.assertFalse(res_batch['is_error'])
        self.assertIn('product_exist', res_batch)

    def test_assign_recent_scan(self):
        """Test assign_recent_scan updates tracking fields"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        self.model.assign_recent_scan(picking.id, 'product.product', 'none', self.product_untracked.id)
        self.assertEqual(picking.barcode_recent_scan, 'product.product')
        self.assertEqual(picking.last_scan_tracking, 'none')
        self.assertEqual(picking.last_scanned_product, self.product_untracked)

    def test_handle_barcode_scan_untracked(self):
        """Test barcode scan handling for untracked product"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        # First scan creates move and line
        self.model._handle_barcode_scan(picking, "", self.product_untracked)
        move = picking.move_ids.filtered(lambda m: m.product_id == self.product_untracked)
        self.assertTrue(move)
        self.assertEqual(len(move.move_line_ids), 1)

        # Second scan increments quantity
        self.model._handle_barcode_scan(picking, "", self.product_untracked)
        self.assertEqual(move.move_line_ids[0].quantity, 2)

    def test_handle_barcode_scan_serial(self):
        """Test barcode scan handling for serial tracked product"""
        picking = self._create_test_picking(self.picking_type_in, self.loc_suppliers, self.loc_stock)
        # First serial scan creates line
        self.model._handle_barcode_scan(picking, "SN-001", self.product_serial)
        move = picking.move_ids.filtered(lambda m: m.product_id == self.product_serial)
        self.assertTrue(move)
        self.assertEqual(move.move_line_ids[0].lot_name, "SN-001")

        # Second distinct serial scan adds new move line
        self.model._handle_barcode_scan(picking, "SN-002", self.product_serial)
        self.assertEqual(len(move.move_line_ids), 2)

        # Duplicate serial scan raises UserError
        with self.assertRaises(UserError):
            self.model._handle_barcode_scan(picking, "SN-001", self.product_serial)

    def test_handle_barcode_scan_lot(self):
        """Test barcode scan handling for lot tracked product"""
        picking = self._create_test_picking(self.picking_type_in, self.loc_suppliers, self.loc_stock)
        # First scan creates lot line
        self.model._handle_barcode_scan(picking, "LOT-A", self.product_lot)
        move = picking.move_ids.filtered(lambda m: m.product_id == self.product_lot)
        self.assertTrue(move)

        # Second scan with same lot increments quantity
        self.model._handle_barcode_scan(picking, "LOT-A", self.product_lot)
        line = move.move_line_ids.filtered(lambda line: line.lot_name == "LOT-A")
        self.assertEqual(line.quantity, 2)

        # Scan with new lot creates new line
        self.model._handle_barcode_scan(picking, "LOT-B", self.product_lot)
        self.assertEqual(len(move.move_line_ids), 2)

    def test_add_stock_move_line_wrapper(self):
        """Test add_stock_move_line entrypoint from client"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        self.model.add_stock_move_line(
            picking.id,
            res_model='product.product',
            data=[{'id': self.product_untracked.id}],
            barcode='PROD_UNTRACKED_01',
        )
        self.assertTrue(picking.move_ids)

    def test_add_stock_location(self):
        """Test adding destination / source location via barcode scan"""
        loc_new = self.env['stock.location'].create({'name': 'SubLocation', 'usage': 'internal'})

        # 1. Incoming: updates destination
        picking_in = self._create_test_picking(self.picking_type_in, self.loc_suppliers, self.loc_stock)
        self.model._handle_barcode_scan(picking_in, "", self.product_untracked)
        self.model.add_stock_location(
            picking_in.id,
            picking_type='incoming',
            data=[{'id': loc_new.id}],
            res_model='stock.location',
        )
        self.assertEqual(picking_in.move_line_ids[0].location_dest_id, loc_new)
        self.assertTrue(picking_in.move_line_ids[0].had_location_by_barcode)

        # 2. Outgoing: updates source
        picking_out = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        self.model._handle_barcode_scan(picking_out, "", self.product_untracked)
        self.model.add_stock_location(
            picking_out.id,
            picking_type='outgoing',
            data=[{'id': loc_new.id}],
            res_model='stock.location',
        )
        self.assertEqual(picking_out.move_line_ids[0].location_id, loc_new)

        # 3. Batch location assignment
        self.model.add_stock_location_batch([picking_out.id], picking_type='outgoing', data=[{'id': loc_new.id}])

    def test_assign_lot_number_and_barcode(self):
        """Test assign_barcode_move_line and create_lot"""
        picking = self._create_test_picking(self.picking_type_in, self.loc_suppliers, self.loc_stock)
        self.model._handle_barcode_scan(picking, "", self.product_serial)
        picking.picking_type_id.use_create_lots = True
        picking.picking_type_id.use_existing_lots = True

        self.model.assign_barcode_move_line(
            picking.id,
            self.product_serial.id,
            barcode='NEW_SN_999',
            res_model='stock.lot',
        )
        line = picking.move_line_ids[0]
        self.assertEqual(line.lot_name, 'NEW_SN_999')

    def test_package_assignment_and_constraints(self):
        """Test assign_package_move_line and UserErrors for reuse / missing products"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        pkg_model = 'stock.package' if 'stock.package' in self.env else 'stock.quant.package'
        package = self.env[pkg_model].create({'name': 'PACK-TEST-001'})

        # Error when no scanned products exist
        with self.assertRaises(UserError):
            self.model.assign_package_move_line(picking.id, data=[{'id': package.id}])

        # Scan a product first
        self.model._handle_barcode_scan(picking, "", self.product_untracked)

        # Assign package successfully
        self.model.assign_package_move_line(picking.id, data=[{'id': package.id}])
        self.assertEqual(picking.move_line_ids[0].result_package_id, package)

        # Error if trying to reuse same package
        with self.assertRaises(UserError):
            self.model.assign_package_move_line(picking.id, data=[{'id': package.id}])

        # Batch package assign on a new picking with scanned product
        picking_batch = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        self.model._handle_barcode_scan(picking_batch, "", self.product_untracked)
        package_batch = self.env[pkg_model].create({'name': 'PACK-BATCH-002'})
        self.model.assign_package_move_line_batch([picking_batch.id], data=[{'id': package_batch.id}])
        self.assertEqual(picking_batch.move_line_ids[0].result_package_id, package_batch)

    def test_action_remove_and_add_by_one(self):
        """Test action_remove_move_line and add_move_line_by_one"""
        picking = self._create_test_picking(self.picking_type_out, self.loc_stock, self.loc_customers)
        self.model._handle_barcode_scan(picking, "", self.product_untracked)
        move = picking.move_ids[0]
        line = move.move_line_ids[0]

        # Add by one
        self.model.add_move_line_by_one(move.id)
        self.assertEqual(line.quantity, 2)

        # Remove line
        self.model.action_remove_move_line(picking.id, line.id, 'stock.move.line')
        self.assertFalse(line.exists())
