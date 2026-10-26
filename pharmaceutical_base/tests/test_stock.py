# -*- coding: utf-8 -*-
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
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import PharmaTestCommon


@tagged('post_install', '-at_install')
class TestPharmaStock(PharmaTestCommon):
    """Lot status, quarantine queue, storage classes and disposition moves."""

    @classmethod
    def setUpClass(cls):
        """Locations, a storage class and its sub-area under WH/Stock."""
        super().setUpClass()
        cls.stock = cls.env.ref('stock.stock_location_stock')
        cls.cold = cls.env['stock.storage.category'].create({'name': 'Cold Chain'})
        cls.cold_area = cls.env['stock.location'].create({
            'name': 'Cold Room', 'usage': 'internal', 'location_id': cls.stock.id,
            'storage_category_id': cls.cold.id,
        })
        cls.rejected = cls.env['stock.location'].create({
            'name': 'Rejected Area', 'usage': 'internal', 'location_id': cls.stock.id,
        })
        cls.supplier = cls.env.ref('stock.stock_location_suppliers')

    def _picking(self, picking_type, src, dest, lot, qty=5.0):
        """A confirmed picking of ``qty`` units of ``lot`` with its move line set."""
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id, 'product_uom_qty': qty,
                'product_uom': self.product.uom_id.id,
                'location_id': src.id, 'location_dest_id': dest.id,
            })],
        })
        picking.action_confirm()
        picking.move_ids.move_line_ids.unlink()
        self.env['stock.move.line'].create({
            'move_id': picking.move_ids.id, 'picking_id': picking.id,
            'product_id': self.product.id, 'product_uom_id': self.product.uom_id.id,
            'lot_id': lot.id, 'quantity': qty, 'picked': True,
            'location_id': src.id, 'location_dest_id': dest.id,
        })
        picking.move_ids.picked = True
        return picking

    def test_lot_status_tracking(self):
        """Status changes record who and when; QC buttons list the lot's orders."""
        lot = self.env['stock.lot'].create({
            'name': 'L-STAT', 'product_id': self.product.id, 'lot_status': 'on_hold',
        })
        self.assertEqual(lot.status_changed_by, self.env.user)
        lot.action_approve_lot()
        self.assertEqual(lot.lot_status, 'approved')
        lot.action_reject_lot()
        self.assertEqual(lot.lot_status, 'rejected')
        self.create_order(lot=lot)
        self.assertEqual(lot.qc_test_count, 1)
        self.assertEqual(lot.action_view_qc_tests()['domain'], [('lot_id', '=', lot.id)])

    def test_receipt_quarantines_lots(self):
        """Validated receipts put their lots in quarantine."""
        lot = self.create_lot(name='L-IN')
        lot.lot_status = 'quarantine'
        receipt = self._picking(self.env.ref('stock.picking_type_in'), self.supplier, self.stock, lot)
        receipt._action_done()
        self.assertEqual((receipt.state, lot.lot_status), ('done', 'quarantine'))

    def test_quarantined_lot_cannot_move(self):
        """Internal moves of a quarantined lot are blocked; QA dispositions are not."""
        lot = self.create_lot(name='L-Q')
        self.env['stock.quant']._update_available_quantity(self.product, self.stock, 5.0, lot_id=lot)
        internal = self.env.ref('stock.picking_type_internal')
        picking = self._picking(internal, self.stock, self.rejected, lot)
        with self.assertRaises(UserError):
            picking._action_done()
        picking.with_context(pharma_qa_disposition=True)._action_done()
        self.assertEqual(picking.state, 'done')

    def test_storage_class_enforcement(self):
        """With enforcement on, a classified product must land in its area."""
        self.env.company.pharma_enforce_storage_class = True
        self.product_tmpl.storage_category_id = self.cold
        self.assertTrue(self.product_tmpl.pharma_enforce_storage_class)
        lot = self.create_lot(name='L-COLD')
        lot.lot_status = 'approved'
        self.env['stock.quant']._update_available_quantity(self.product, self.stock, 5.0, lot_id=lot)
        internal = self.env.ref('stock.picking_type_internal')
        wrong = self._picking(internal, self.stock, self.rejected, lot, 2.0)
        with self.assertRaises(UserError):
            wrong._action_done()
        right = self._picking(internal, self.stock, self.cold_area, lot, 2.0)
        right._action_done()
        self.assertEqual(right.move_line_ids.pharma_storage_category_id, self.cold)
        self.assertEqual(right.move_line_ids.pharma_required_storage_category_id, self.cold)

    def test_putaway_to_storage_class(self):
        """Putaway resolves the storage class into its sub-area."""
        self.product_tmpl.storage_category_id = self.cold
        self.assertEqual(self.stock._get_putaway_strategy(self.product, quantity=1), self.cold_area)
        self.assertEqual(self.cold_area._pharma_storage_categories(), self.cold)

    def test_disposition_transfer(self):
        """A failed incoming QC order moves the lot to the rejected location."""
        self.env.company.pharma_rejected_location_id = self.rejected
        lot = self.create_lot(name='L-REJ')
        self.env['stock.quant']._update_available_quantity(self.product, self.stock, 4.0, lot_id=lot)
        self.env['stock.quant']._update_available_quantity(self.product, self.rejected, 1.0, lot_id=lot)
        order = self.create_order(lot=lot)
        order.action_start_test()
        order.with_user(self.qa_user).action_reject()
        quants = self.env['stock.quant'].search([('lot_id', '=', lot.id), ('quantity', '>', 0)])
        self.assertEqual(quants.location_id, self.rejected)
        self.assertEqual(sum(quants.mapped('quantity')), 5.0)
        self.assertFalse(lot._pharma_create_disposition_transfer(self.rejected))
        self.assertFalse(lot._pharma_create_disposition_transfer(self.env['stock.location']))

    def test_disposition_skipped_outside_incoming(self):
        """Finished-goods orders and orders without stock make no transfer."""
        spec = self.create_spec(self.product_tmpl, 'finished')
        spec.action_submit_review()
        spec.with_user(self.qa_user).action_approve()
        order = self.create_order(stage='finished')
        order._pharma_dispose_rejected()
        self.assertFalse(order._pharma_rejection_deferred())

    def test_quant_queue_actions(self):
        """Quarantine queue: create QC orders, open moves and lots."""
        lot = self.create_lot(name='L-QQ')
        self.env['stock.quant']._update_available_quantity(self.product, self.stock, 3.0, lot_id=lot)
        quant = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
        self.assertFalse(quant.has_incoming_qc)
        self.assertEqual(quant.qc_test_order_count, 0)
        result = quant.action_quant_create_qc_test()
        self.assertEqual(result['tag'], 'display_notification')
        quant.invalidate_recordset()
        self.assertTrue(quant.has_incoming_qc)
        self.assertEqual(quant.action_view_qc_test_orders()['view_mode'], 'form')
        with self.assertRaises(UserError):
            quant.action_quant_create_qc_test()
        self.assertEqual(quant.move_line_count, 0)
        self.assertEqual(quant.action_view_stock_moves()['res_model'], 'stock.move.line')
        self.assertEqual(quant.action_quant_open_lot()['res_id'], lot.id)

    def test_quant_without_lot(self):
        """A quant without a lot uses the product for its counts and refuses lot actions."""
        plain = self.env['product.product'].create({'name': 'Gloves', 'is_storable': True})
        self.env['stock.quant']._update_available_quantity(plain, self.stock, 2.0)
        quant = self.env['stock.quant'].search([('product_id', '=', plain.id)])
        self.assertFalse(quant.has_incoming_qc)
        self.assertEqual(quant._pharma_move_line_domain()[0], ('product_id', '=', plain.id))
        self.assertIn(('product_id', '=', plain.product_tmpl_id.id),
                      quant.action_view_qc_test_orders()['domain'])
        with self.assertRaises(UserError):
            quant.action_quant_open_lot()
        with self.assertRaises(UserError):
            quant.action_quant_create_qc_test()
        empty = self.env['stock.quant'].new({})
        empty._compute_has_incoming_qc()
        empty._compute_qc_test_order_count()
        self.assertEqual(empty.qc_test_order_count, 0)

    def test_purchase_merges_identical_lines(self):
        """Identical purchase lines are merged on create and on write."""
        partner = self.env['res.partner'].create({'name': 'API Supplier'})
        line = {'product_id': self.product.id, 'product_qty': 1}
        order = self.env['purchase.order'].create({
            'partner_id': partner.id, 'order_line': [(0, 0, line), (0, 0, dict(line, product_qty=2))],
        })
        self.assertEqual(order.order_line.product_qty, 3)
        order.write({'order_line': [(0, 0, dict(line, product_qty=4))]})
        self.assertEqual(order.order_line.product_qty, 7)


@tagged('post_install', '-at_install')
class TestCompanyAndProduct(PharmaTestCommon):
    """Company GMP settings and pharma product rules."""

    def test_company_constraints(self):
        """The rejected location must be internal and scores within 0-100."""
        company = self.env.company
        with self.assertRaises(ValidationError):
            company.pharma_rejected_location_id = self.env.ref('stock.stock_location_suppliers')
        with self.assertRaises(ValidationError):
            company.pharma_vendor_approval_percentage = 0
        with self.assertRaises(ValidationError):
            company.pharma_training_passing_score = 120

    def test_pharma_product_tracking(self):
        """Pharma products are lot tracked and get a lot sequence."""
        form = Form(self.env['product.template'])
        form.name = 'Lactose'
        form.is_storable = True
        form.product_type_pharma = 'excipient'
        self.assertEqual(form.tracking, 'lot')
        tmpl = form.save()
        self.assertTrue(tmpl.lot_sequence_id)
        with self.assertRaises(ValidationError):
            tmpl.tracking = 'none'
        plain = self.env['product.template'].create({'name': 'Plain', 'is_storable': True})
        plain.write({'tracking': 'lot'})
        self.assertTrue(plain.lot_sequence_id)
        plain.lot_sequence_id = False
        self.env['product.template']._backfill_lot_sequences()
        self.assertTrue(plain.lot_sequence_id)

    def test_storage_class_required(self):
        """With enforcement on, a pharma product needs a storage class."""
        self.env.company.pharma_enforce_storage_class = True
        with self.assertRaises(ValidationError):
            self.env['product.template'].create({
                'name': 'Insulin', 'is_storable': True, 'tracking': 'lot', 'product_type_pharma': 'api',
            })

    def test_product_searches(self):
        """Products can be searched by passed QC and approved formula."""
        Template = self.env['product.template']
        Product = self.env['product.product']
        self.assertNotIn(self.product_tmpl, Template.search([('has_passed_qc_test', '=', True)]))
        self.assertIn(self.product_tmpl, Template.search([('has_passed_qc_test', '=', False)]))
        self.assertIn(self.product_tmpl, Template.search([('has_approved_bom', '=', False)]))
        self.assertNotIn(self.product_tmpl, Template.search([('has_approved_bom', '=', True)]))
        order = self.create_order()
        order.action_start_test()
        order.result_line_ids.write({'actual_value': 100.0})
        order.with_user(self.qa_user).action_approve()
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'operation_ids': [(0, 0, {'name': 'Mix', 'workcenter_id': self.env['mrp.workcenter'].create(
                {'name': 'WC'}).id})],
        })
        bom.with_user(self.qa_user).sudo().action_approve_formula()
        self.assertTrue(self.product_tmpl.has_approved_bom)
        self.assertEqual(self.product_tmpl.qc_spec_count, 1)
        for model, record in ((Template, self.product_tmpl), (Product, self.product)):
            self.assertIn(record, model.search([('has_passed_qc_test', '=', True)]))
            self.assertNotIn(record, model.search([('has_passed_qc_test', '!=', True)]))
            self.assertIn(record, model.search([('has_approved_bom', '=', True)]))
            self.assertNotIn(record, model.search([('has_approved_bom', '=', False)]))
