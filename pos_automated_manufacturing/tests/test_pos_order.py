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

from odoo import fields
from odoo.tests import common


class TestPosOrder(common.TransactionCase):
    """
    Test suite for validating the creation and linking of MRP orders from POS orders.
    Exercises the _process_order hook, guards against draft/duplicate creation,
    and ensures refund lines are excluded.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product for POS MRP',
            'type': 'consu',
        })

        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
            'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': cls.component.id,
                'product_qty': 1.0,
            })],
        })

        cls.pos_config = cls.env.ref('point_of_sale.pos_config_main', raise_if_not_found=False)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config',
            })

        cls.payment_method = cls.pos_config.payment_method_ids[:1]
        if not cls.payment_method:
            cls.payment_method = cls.env['pos.payment.method'].search([('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.payment_method:
            cls.payment_method = cls.env['pos.payment.method'].search([], limit=1)
        if not cls.payment_method:
            journal = cls.env['account.journal'].search([('type', 'in', ['cash', 'bank']), ('company_id', '=', cls.env.company.id)], limit=1)
            cls.payment_method = cls.env['pos.payment.method'].create({
                'name': 'Test POS Cash',
                'journal_id': journal.id if journal else False,
                'company_id': cls.env.company.id,
            })
        if cls.payment_method not in cls.pos_config.payment_method_ids:
            cls.pos_config.write({'payment_method_ids': [(4, cls.payment_method.id)]})

        cls.session = cls.env['pos.session'].search([
            ('config_id', '=', cls.pos_config.id),
            ('state', '=', 'opened')
        ], limit=1)

        if not cls.session:
            cls.session = cls.env['pos.session'].create({
                'config_id': cls.pos_config.id,
                'user_id': cls.env.uid,
            })

    def _prepare_pos_order_data(self, qty=2.0, state='paid', name="Order Test"):
        total = 100.0 * qty
        data = {
            'session_id': self.session.id,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': qty,
                'price_unit': 100.0,
                'price_subtotal': total,
                'price_subtotal_incl': total,
            })],
            'amount_total': total,
            'amount_tax': 0.0,
            'amount_paid': total if state == 'paid' else 0.0,
            'amount_return': 0.0,
            'name': name,
            'state': state,
        }
        if state in ['paid', 'done', 'invoiced'] and self.payment_method:
            data['payment_ids'] = [(0, 0, {
                'amount': total,
                'name': 'Test Payment',
                'payment_method_id': self.payment_method.id,
            })]
        return data

    def test_01_process_order_creates_and_links_mrp(self):
        """Test that _process_order triggers confirmed MRP order and links both records."""
        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        order_data = self._prepare_pos_order_data(qty=2.0, state='paid', name="Order Test 01")
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)

        self.assertEqual(pos_order.mrp_production_count, 1, "Exactly one MRP order should be linked.")
        mrp_order = pos_order.mrp_production_ids
        self.assertTrue(mrp_order, "MRP order should be created and linked.")
        self.assertEqual(mrp_order.pos_order_id.id, pos_order.id, "MRP order must link back to pos.order.")
        self.assertEqual(mrp_order.product_id.id, self.product.id)
        self.assertEqual(mrp_order.product_qty, 2.0)
        self.assertEqual(mrp_order.state, 'confirmed', "MRP order should be confirmed.")
        self.assertEqual(pos_order.lines[0].mrp_production_id.id, mrp_order.id, "Line must link to MO.")

        # Test smart button action
        action = pos_order.action_view_mrp_production()
        self.assertEqual(action.get('res_id'), mrp_order.id)

    def test_02_process_order_done_state(self):
        """Test creating a done MRP order from POS order line via _process_order."""
        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': True})

        order_data = self._prepare_pos_order_data(qty=3.0, state='paid', name="Order Test 02")
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)

        self.assertEqual(pos_order.mrp_production_count, 1)
        mrp_order = pos_order.mrp_production_ids
        self.assertEqual(mrp_order.state, 'done', "MRP order should be automatically marked as done.")
        self.assertEqual(mrp_order.pos_order_id.id, pos_order.id)

    def test_03_draft_guard_and_no_duplicate_on_sync(self):
        """Test that draft orders do not generate MOs, and re-syncing does not create duplicates."""
        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        # 1. Draft sync: no MO should be generated
        order_data = self._prepare_pos_order_data(qty=1.0, state='draft', name="Order Draft Sync")
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)
        self.assertEqual(pos_order.mrp_production_count, 0, "Draft orders must not create MRP orders.")

        # 2. Payment transition: creates MO
        if self.payment_method:
            pos_order.add_payment({
                'pos_order_id': pos_order.id,
                'amount': pos_order.amount_total,
                'payment_date': fields.Datetime.now(),
                'payment_method_id': self.payment_method.id,
            })
        pos_order.action_pos_order_paid()
        self.assertEqual(pos_order.mrp_production_count, 1, "MO should be created once order is paid.")

        # 3. Repeated sync/call: guard prevents duplicate MO creation
        pos_order.create_mrp_orders()
        self.assertEqual(pos_order.mrp_production_count, 1, "Duplicate MO must not be created on repeat calls.")

    def test_04_refund_negative_qty_excluded(self):
        """Test that refund lines with negative qty and lines with zero qty are excluded from MO creation."""
        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        order_data = {
            'session_id': self.session.id,
            'lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': -1.0,
                    'price_unit': 100.0,
                    'price_subtotal': -100.0,
                    'price_subtotal_incl': -100.0,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': 0.0,
                    'price_unit': 100.0,
                    'price_subtotal': 0.0,
                    'price_subtotal_incl': 0.0,
                }),
            ],
            'amount_total': -100.0,
            'amount_tax': 0.0,
            'amount_paid': -100.0,
            'amount_return': 0.0,
            'name': "Order Refund and Zero Qty",
            'state': 'paid',
        }
        if self.payment_method:
            order_data['payment_ids'] = [(0, 0, {
                'amount': -100.0,
                'name': 'Refund Payment',
                'payment_method_id': self.payment_method.id,
            })]
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)

        self.assertEqual(pos_order.mrp_production_count, 0, "Lines with non-positive qty must not create MOs.")

    def test_05_multiple_lines_and_action_view_domain(self):
        """Test creating multiple MOs from an order and action_view_mrp_production domain branch."""
        product_2 = self.env['product.product'].create({
            'name': 'Second Test Product',
            'type': 'consu',
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': product_2.product_tmpl_id.id,
            'product_id': product_2.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 1.0,
            })],
        })

        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})
        product_2.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        order_data = {
            'session_id': self.session.id,
            'lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 100.0,
                    'price_subtotal': 100.0,
                    'price_subtotal_incl': 100.0,
                }),
                (0, 0, {
                    'product_id': product_2.id,
                    'qty': 2.0,
                    'price_unit': 50.0,
                    'price_subtotal': 100.0,
                    'price_subtotal_incl': 100.0,
                }),
            ],
            'amount_total': 200.0,
            'amount_tax': 0.0,
            'amount_paid': 200.0,
            'amount_return': 0.0,
            'name': "Order Multiple Lines",
            'state': 'paid',
        }
        if self.payment_method:
            order_data['payment_ids'] = [(0, 0, {
                'amount': 200.0,
                'name': 'Order Multiple Lines Payment',
                'payment_method_id': self.payment_method.id,
            })]

        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)

        self.assertEqual(pos_order.mrp_production_count, 2, "Two MRP orders should be created.")
        action = pos_order.action_view_mrp_production()
        self.assertIn('domain', action, "Action should return domain when multiple MRP orders exist.")
        domain_ids = [val[2] for val in action['domain'] if val[0] == 'id'][0]
        self.assertEqual(set(domain_ids), set(pos_order.mrp_production_ids.ids))


    def test_06_unconfigured_product_skipped(self):
        """Test that products without to_create_mrp enabled are ignored during MRP creation."""
        self.product.product_tmpl_id.write({'to_create_mrp': False, 'create_mrp_done': False})

        order_data = self._prepare_pos_order_data(qty=1.0, state='paid', name="Order Unconfigured Product")
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)

        self.assertEqual(pos_order.mrp_production_count, 0, "Products without to_create_mrp should not generate MOs.")

    def test_07_process_order_done_invoiced_state(self):
        """Test that an order transitioned to 'invoiced' or 'done' state maintains linked MRP orders."""
        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        order_data = self._prepare_pos_order_data(qty=1.0, state='paid', name="Order Invoiced State")
        pos_order_id = self.env['pos.order']._process_order(order_data, False)
        pos_order = self.env['pos.order'].browse(pos_order_id)
        self.assertEqual(pos_order.mrp_production_count, 1)

        pos_order.write({'state': 'invoiced'})
        self.assertEqual(pos_order.state, 'invoiced')
        # Calling create_mrp_orders on invoiced order respects duplicate guard
        pos_order.create_mrp_orders()
        self.assertEqual(pos_order.mrp_production_count, 1, "Invoiced orders must not create duplicate MRP orders.")

    def test_08_cashier_without_mrp_rights(self):
        """Test that a cashier user without MRP rights can process order and read count without AccessError."""
        group_user = self.env.ref('base.group_user')
        group_pos_user = self.env.ref('point_of_sale.group_pos_user')
        cashier = self.env['res.users'].create({
            'name': 'POS Cashier Only',
            'login': 'pos_cashier_test',
            'email': 'cashier@test.com',
            'groups_id': [(6, 0, [group_user.id, group_pos_user.id])],
        })

        self.product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': False})

        order_data = self._prepare_pos_order_data(qty=1.0, state='paid', name="Cashier Non-MRP Order")
        # Process order as the cashier user without MRP access
        pos_order_id = self.env['pos.order'].with_user(cashier)._process_order(order_data, False)
        pos_order = self.env['pos.order'].with_user(cashier).browse(pos_order_id)

        # compute_sudo ensures reading mrp_production_count succeeds for cashier
        self.assertEqual(pos_order.mrp_production_count, 1)
        self.assertTrue(pos_order.sudo().mrp_production_ids)




