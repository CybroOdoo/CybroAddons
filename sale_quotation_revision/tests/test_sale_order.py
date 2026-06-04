# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'sale_quotation_revision')
class TestSaleOrderRevision(TransactionCase):
    """Tests for SaleOrder revision fields and methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'list_price': 100.0,
        })

    def _make_order(self, name=None):
        """Helper: create a draft sale order with one line."""
        vals = {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        }
        if name:
            vals['name'] = name
        return self.env['sale.order'].create(vals)

    # ------------------------------------------------------------------
    # 1. Field presence & defaults
    # ------------------------------------------------------------------

    def test_new_order_defaults(self):
        """All revision fields must default to False / 0 on a new order."""
        order = self._make_order()
        self.assertFalse(order.is_revised)
        self.assertFalse(order.org_sale_id)
        self.assertFalse(order.rev_confirm)
        self.assertEqual(order.rev_ord_count, 0)
        self.assertFalse(order.rev_sale_ids)

    # ------------------------------------------------------------------
    # 2. action_revise_quotation
    # ------------------------------------------------------------------

    def test_revise_sets_is_revised(self):
        """Calling action_revise_quotation must set is_revised=True on the original."""
        order = self._make_order()
        order.action_revise_quotation()
        self.assertTrue(order.is_revised)

    def test_revise_creates_new_order(self):
        """action_revise_quotation must create exactly one new sale.order."""
        order = self._make_order()
        before = self.env['sale.order'].search_count([])
        order.action_revise_quotation()
        after = self.env['sale.order'].search_count([])
        self.assertEqual(after, before + 1)

    def test_revise_links_org_sale_id(self):
        """The revised order must have org_sale_id pointing to the original."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertEqual(len(revised), 1)
        self.assertEqual(revised.org_sale_id, order)

    def test_revise_name_format_first_revision(self):
        """First revision name must follow the '<original>/R1' pattern."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertTrue(revised.name.endswith('/R1'),
                        f"Expected name ending '/R1', got '{revised.name}'")

    def test_revise_returns_act_window(self):
        """action_revise_quotation must return an ir.actions.act_window dict."""
        order = self._make_order()
        result = order.action_revise_quotation()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'sale.order')
        self.assertEqual(result.get('view_mode'), 'form')

    def test_revise_returns_new_order_id(self):
        """The returned action must point to the newly created revision."""
        order = self._make_order()
        result = order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertEqual(result.get('res_id'), revised.id)

    def test_revise_copies_order_lines(self):
        """The revised order must carry over the original order lines."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertEqual(len(revised.order_line), len(order.order_line))

    # ------------------------------------------------------------------
    # 3. compute_rev_ord_count
    # ------------------------------------------------------------------

    def test_rev_ord_count_zero_initially(self):
        """rev_ord_count must be 0 for a fresh order with no revisions."""
        order = self._make_order()
        self.assertEqual(order.rev_ord_count, 0)

    def test_rev_ord_count_increments(self):
        """rev_ord_count must increase with each revision created.
        """
        order = self._make_order()
        self.assertEqual(order.rev_ord_count, 0)
        order.action_revise_quotation()
        order.invalidate_recordset(['rev_ord_count', 'rev_sale_ids'])
        self.assertEqual(order.rev_ord_count, 1)
        order.action_revise_quotation()
        order.invalidate_recordset(['rev_ord_count', 'rev_sale_ids'])
        self.assertEqual(order.rev_ord_count, 2)

    def test_rev_ord_count_on_revised_order_is_zero(self):
        """The revised copy itself must start with rev_ord_count == 0."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertEqual(revised.rev_ord_count, 0)

    # ------------------------------------------------------------------
    # 4. get_revised_orders
    # ------------------------------------------------------------------

    def test_get_revised_orders_returns_act_window(self):
        """get_revised_orders must return an ir.actions.act_window dict."""
        order = self._make_order()
        order.action_revise_quotation()
        result = order.get_revised_orders()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'sale.order')

    def test_get_revised_orders_domain_filters_by_origin(self):
        """get_revised_orders domain must filter by org_sale_id == self.id."""
        order = self._make_order()
        order.action_revise_quotation()
        result = order.get_revised_orders()
        self.assertIn(('org_sale_id', '=', order.id), result.get('domain', []))

    def test_get_revised_orders_requires_single_record(self):
        """get_revised_orders must call ensure_one() and raise on multi-record set."""
        o1 = self._make_order()
        o2 = self._make_order()
        with self.assertRaises(Exception):
            (o1 | o2).get_revised_orders()

    # ------------------------------------------------------------------
    # 5. unlink override
    # ------------------------------------------------------------------

    def test_unlink_raises_when_revised_with_children(self):
        """Deleting an order that is_revised and has rev_sale_ids must raise UserError."""
        order = self._make_order()
        order.action_revise_quotation()
        self.assertTrue(order.is_revised)
        self.assertGreater(order.rev_ord_count, 0)
        with self.assertRaises(UserError):
            order.unlink()

    def test_unlink_error_message_mentions_revised(self):
        """UserError message must mention revised orders."""
        order = self._make_order()
        order.action_revise_quotation()
        with self.assertRaises(UserError) as ctx:
            order.unlink()
        self.assertIn('revised', str(ctx.exception).lower())

    def test_unlink_allowed_after_deleting_revisions(self):
        """After all revision children are removed, the original can be deleted."""
        order = self._make_order()
        order.action_revise_quotation()
        # Delete the revision first
        order.rev_sale_ids.unlink()
        # Now the original (is_revised=True but no children) can be deleted
        order_id = order.id
        order.unlink()
        self.assertFalse(self.env['sale.order'].browse(order_id).exists())

    # ------------------------------------------------------------------
    # 6. action_confirm with revision logic
    # ------------------------------------------------------------------

    def test_confirm_with_related_opens_wizard(self):
        """Confirming an order that has open related revisions must open the wizard."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        # Try confirming the revised order (which has the original as related)
        result = revised.action_confirm()
        # Must return a wizard window, not None
        self.assertIsNotNone(result)
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'sale.order.confirm.wizard')

    def test_confirm_sets_rev_confirm_false_initially(self):
        """A freshly revised order must have rev_confirm=False."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        self.assertFalse(revised.rev_confirm)

    # ------------------------------------------------------------------
    # 7. get_related_orders
    # ------------------------------------------------------------------

    def test_get_related_orders_includes_open_revisions(self):
        """get_related_orders must include open (draft) sibling revisions."""
        order = self._make_order()
        order.action_revise_quotation()
        order.action_revise_quotation()
        revisions = order.rev_sale_ids
        r1, r2 = revisions[0], revisions[1]
        related = r1.get_related_orders(r1)
        # r2 is an open sibling via org_sale_id.rev_sale_ids
        self.assertIn(r2, related)

    def test_get_related_orders_excludes_cancelled(self):
        """get_related_orders must not include cancelled orders."""
        order = self._make_order()
        order.action_revise_quotation()
        order.action_revise_quotation()
        r1, r2 = order.rev_sale_ids[0], order.rev_sale_ids[1]
        r2._action_cancel()
        related = r1.get_related_orders(r1)
        self.assertNotIn(r2, related)

    def test_get_related_orders_excludes_confirmed(self):
        """get_related_orders must not include already-confirmed (sale) orders."""
        order = self._make_order()
        order.action_revise_quotation()
        order.action_revise_quotation()
        r1, r2 = order.rev_sale_ids[0], order.rev_sale_ids[1]
        r2.rev_confirm = True
        r2.action_confirm()
        related = r1.get_related_orders(r1)
        self.assertNotIn(r2, related)

    def test_get_related_orders_includes_open_origin(self):
        """get_related_orders must include the original order if it is still open."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        related = revised.get_related_orders(revised)
        self.assertIn(order, related)

    def test_get_related_orders_excludes_confirmed_origin(self):
        """get_related_orders must not include the origin if it is already confirmed."""
        order = self._make_order()
        order.rev_confirm = True
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        related = revised.get_related_orders(revised)
        self.assertNotIn(order, related)

    # ------------------------------------------------------------------
    # 8. copy behaviour (is_revised / rev_confirm must NOT be copied)
    # ------------------------------------------------------------------

    def test_copy_does_not_propagate_is_revised(self):
        """Copying a revised order must not carry over is_revised=True."""
        order = self._make_order()
        order.action_revise_quotation()
        self.assertTrue(order.is_revised)
        copied = order.copy()
        self.assertFalse(copied.is_revised)

    def test_copy_does_not_propagate_org_sale_id(self):
        """Copying a revision must not carry over the org_sale_id link."""
        order = self._make_order()
        order.action_revise_quotation()
        revised = order.rev_sale_ids
        copied = revised.copy()
        self.assertFalse(copied.org_sale_id)