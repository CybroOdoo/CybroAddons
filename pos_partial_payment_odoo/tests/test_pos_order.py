from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('-at_install', 'post_install')
class TestPosOrder(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()

    def _create_order(self, amount_paid=50.0, state='draft',
                      is_partial_payment=True, config=None):
        config = config or self.config
        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.session.id,
            'partner_id': self.customer.id,
            'pricelist_id': config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': amount_paid,
            'amount_return': 0.0,
            'state': state,
            'is_partial_payment': is_partial_payment,
            'last_order_preparation_change': '{}',
        })

    def test_compute_due_amount_uses_order_paid_amount_without_invoice(self):
        order = self._create_order(amount_paid=40.0)

        order._compute_due_amount()

        self.assertEqual(order.due_amount, 60.0)

    def test_compute_due_amount_uses_invoice_residual_when_invoice_exists(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice line',
                'quantity': 1.0,
                'price_unit': 100.0,
            })],
        })
        order = self._create_order(amount_paid=10.0)
        order.account_move = invoice

        order._compute_due_amount()

        self.assertEqual(order.amount_paid, 0.0)
        self.assertEqual(order.due_amount, 100.0)

    def test_order_fields_adds_partial_payment_flag(self):
        result = self.env['pos.order']._order_fields({
            'is_partial_payment': True,
        })

        self.assertTrue(result['is_partial_payment'])

    def test_action_pos_order_paid_allows_underpaid_order_when_partial_enabled(self):
        self.env['pos.config'].search([]).write({'partial_payment': False})
        self.config.partial_payment = True
        order = self._create_order(amount_paid=25.0)

        result = order.action_pos_order_paid()

        self.assertTrue(result)
        self.assertEqual(order.state, 'paid')

    def test_action_pos_order_paid_rejects_underpaid_order_when_partial_disabled(self):
        self.env['pos.config'].search([]).write({'partial_payment': False})
        order = self._create_order(amount_paid=25.0)

        with self.assertRaises(UserError):
            order.action_pos_order_paid()

    def test_search_partial_order_ids_returns_only_partial_matching_orders(self):
        partial_order = self._create_order(state='paid', is_partial_payment=True)
        self._create_order(state='paid', is_partial_payment=False)
        self._create_order(state='draft', is_partial_payment=True)

        result = self.env['pos.order'].search_partial_order_ids(
            self.config.id, [], limit=10, offset=0,
        )

        self.assertEqual(result['totalCount'], 1)
        self.assertEqual(result['ordersInfo'], [
            [partial_order.id, partial_order.write_date.isoformat()],
        ])
