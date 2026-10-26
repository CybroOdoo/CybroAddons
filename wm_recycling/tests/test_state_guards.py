"""Recycling order state guards and the done-order lock (audit Medium findings)."""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_recycling')
class TestRecyclingStateGuards(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Guard PET', 'is_waste_material': True})
        cls.recovered = cls.env['product.product'].create({'name': 'Guard Flakes'})

    def _order(self):
        batch = self.env['waste.batch'].create({
            'line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 10.0})]})
        # put the batch in stock without running the whole receiving workflow
        self.env.cr.execute("UPDATE waste_batch SET status = 'received', is_received = TRUE WHERE id = %s", [batch.id])
        batch.invalidate_recordset()
        order = self.env['recycling.order'].create({'waste_batch_id': batch.id})
        self.env['recycling.line'].create({
            'order_id': order.id, 'product_id': self.recovered.id,
            'uom_id': self.recovered.uom_id.id, 'expected_qty': 5.0})
        return order

    def test_confirm_and_cancel_cannot_be_repeated(self):
        order = self._order()
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        with self.assertRaises(UserError):
            order.action_confirm()
        order.action_cancel()
        self.assertEqual(order.state, 'cancelled')
        with self.assertRaises(UserError):
            order.action_cancel()

    def test_done_order_is_read_only(self):
        order = self._order()
        order.write({'state': 'done'})
        with self.assertRaises(UserError):
            order.write({'date_start': '2026-01-01'})
        with self.assertRaises(UserError):
            order.line_ids.write({'recovered_qty': 99.0})
        with self.assertRaises(UserError):
            order.line_ids.unlink()
