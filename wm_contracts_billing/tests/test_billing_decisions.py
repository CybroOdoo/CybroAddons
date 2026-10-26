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
from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestServiceRequestProcessingRights(TransactionCase):
    """Decision 2: only dispatchers, operations managers, contract managers
    and WM admins may approve / reject / complete service requests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Decision Request Customer'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Decision Request Site', 'partner_id': cls.partner.id})
        cls.allowed_users = [
            new_test_user(cls.env, login='dec_dispatcher', groups='base.group_user,wm_base.group_wm_dispatcher'),
            new_test_user(cls.env, login='dec_ops_manager', groups='base.group_user,wm_base.group_wm_ops_manager'),
            new_test_user(cls.env, login='dec_contract_mgr',
                          groups='base.group_user,wm_contracts_billing.group_wm_contract_manager'),
            new_test_user(cls.env, login='dec_wm_admin', groups='base.group_user,wm_base.group_wm_admin'),
        ]
        cls.denied_users = [
            new_test_user(cls.env, login='dec_driver', groups='base.group_user,wm_base.group_wm_driver'),
            new_test_user(cls.env, login='dec_recycler', groups='base.group_user,wm_base.group_wm_recycler'),
            new_test_user(cls.env, login='dec_finance', groups='base.group_user,wm_base.group_wm_finance'),
            new_test_user(cls.env, login='dec_internal', groups='base.group_user'),
        ]

    def _request(self, state='submitted'):
        req = self.env['wm.portal.service.request'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'request_type': 'container_swap',
            'requested_date': fields.Date.today(),
        })
        req.state = state
        return req

    def test_allowed_groups_can_process(self):
        for user in self.allowed_users:
            with self.subTest(user=user.login):
                req = self._request()
                req.with_user(user).action_approve()
                self.assertEqual(req.state, 'approved')
                req.with_user(user).action_complete()
                self.assertEqual(req.state, 'completed')
                req = self._request()
                req.with_user(user).action_reject()
                self.assertEqual(req.state, 'rejected')

    def test_other_users_can_view_but_not_process(self):
        for user in self.denied_users:
            with self.subTest(user=user.login):
                req = self._request()
                # Viewing is still allowed
                self.assertEqual(req.with_user(user).read(['state'])[0]['state'], 'submitted')
                with self.assertRaises(AccessError):
                    req.with_user(user).action_approve()
                with self.assertRaises(AccessError):
                    req.with_user(user).action_reject()
                approved = self._request(state='approved')
                with self.assertRaises(AccessError):
                    approved.with_user(user).action_complete()
                self.assertEqual(req.state, 'submitted')
                self.assertEqual(approved.state, 'approved')

    def test_sudo_flows_still_allowed(self):
        req = self._request()
        req.with_user(self.denied_users[-1]).sudo().action_approve()
        self.assertEqual(req.state, 'approved')
        # Portal-style cancellation (sudo action_cancel) is unaffected
        req2 = self._request()
        req2.with_user(self.denied_users[-1]).sudo().action_cancel()
        self.assertEqual(req2.state, 'cancelled')

    def test_form_buttons_restricted_to_processing_groups(self):
        Request = self.env['wm.portal.service.request']
        for user, visible in ([(u, True) for u in self.allowed_users]
                              + [(u, False) for u in self.denied_users]):
            with self.subTest(user=user.login):
                arch = Request.with_user(user).get_views([(False, 'form')])['views']['form']['arch']
                for method in ('action_approve', 'action_open_reject_wizard', 'action_complete', 'action_cancel'):
                    self.assertEqual('name="%s"' % method in arch, visible, method)

    def test_reject_only_from_submitted_and_keeps_reason(self):
        user = self.allowed_users[0]
        req = self._request()
        wizard = self.env['wm.portal.request.reject.wizard'].with_user(user).create({
            'request_id': req.id, 'reason': 'Outside the contract area'})
        wizard.action_reject()
        self.assertEqual(req.state, 'rejected')
        self.assertEqual(req.rejection_reason, 'Outside the contract area')
        approved = self._request()
        approved.with_user(user).action_approve()
        with self.assertRaises(UserError):
            approved.with_user(user).action_reject(reason='Too late')
        self.assertEqual(approved.state, 'approved')

    def test_cancel_allowed_states_and_group(self):
        user = self.allowed_users[0]
        for state in ('rejected', 'completed', 'in_progress'):
            req = self._request(state=state)
            with self.assertRaises(UserError):
                req.with_user(user).action_cancel()
        req = self._request()
        with self.assertRaises(AccessError):
            req.with_user(self.denied_users[-1]).action_cancel()
        req.with_user(user).action_cancel()
        self.assertEqual(req.state, 'cancelled')

    def test_cancel_approved_cancels_generated_order_and_event(self):
        user = self.allowed_users[0]
        req = self._request()
        req.request_type = 'extra_pickup'
        req.with_user(user).action_approve()
        order = req.collection_order_id
        self.assertTrue(order)
        req.with_user(user).action_cancel()
        self.assertEqual(req.state, 'cancelled')
        self.assertEqual(order.state, 'cancelled')
        events = self.env['wm.billable.event'].search([('portal_request_id', '=', req.id)])
        self.assertTrue(events)
        self.assertEqual(set(events.mapped('state')), {'cancelled'})


@tagged('post_install', '-at_install', 'wm_billing')
class TestDashboardRevenuePostedInvoices(TransactionCase):
    """Decision 5: an order whose invoice is still draft counts as ORDER
    revenue; once the invoice is posted it only counts as invoice revenue."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Decision Dashboard Customer'})
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Decision Dash Cat', 'code': 'DDC', 'price': 2.0})

    def _completed_order(self):
        Order = self.env['wm.collection.order']
        order = Order.create({
            'partner_id': self.partner.id,
            'scheduled_start': fields.Datetime.now(),
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 50.0, 'price': 2.0})],
        })
        order.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        return order

    def _draft_invoice(self, amount):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.context_today(self.env['account.move']),
            'invoice_line_ids': [(0, 0, {
                'name': 'Decision collection fee',
                'quantity': 1.0,
                'price_unit': amount,
                'tax_ids': [(6, 0, [])],
            })],
        })

    def _data(self):
        self.env.flush_all()
        return self.env['wm.dashboard'].get_dashboard_data('today')

    def test_exclusion_domain_covers_all_invoice_links(self):
        domain = self.env['wm.dashboard']._get_order_revenue_exclusion_domain()
        self.assertEqual(domain[0], '!')
        paths = [leaf[0] for leaf in domain if isinstance(leaf, (list, tuple))]
        self.assertEqual(sorted(paths), sorted([
            'consolidated_invoice_id.invoice_id.state',
            'billing_run_line_id.invoice_id.state',
            'billing_run_line_id.invoice_not_required',
            'direct_invoice_id.state',
        ]))
        self.assertEqual(self._data()['order_revenue_domain'], domain)

    def test_draft_invoice_counts_as_order_revenue_until_posted(self):
        if not self.env['account.journal'].search([
                ('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1):
            self.skipTest('No sales journal configured')
        before = self._data()
        order = self._completed_order()
        amount = order.total_amount
        self.assertTrue(amount)

        invoice = self._draft_invoice(amount)
        order.sudo().write({'direct_invoice_id': invoice.id})
        self.assertTrue(order.is_billed)

        # Draft invoice: still order revenue, no invoice revenue yet
        draft_data = self._data()
        self.assertAlmostEqual(
            draft_data['revenue_collection'] - before['revenue_collection'], amount, places=2)
        self.assertAlmostEqual(
            draft_data['revenue_invoice'] - before['revenue_invoice'], 0.0, places=2)
        Order = self.env['wm.collection.order']
        self.assertIn(order, Order.search([('id', '=', order.id)] + draft_data['order_revenue_domain']))

        # Posted invoice: only invoice revenue (no double counting)
        invoice.action_post()
        posted_data = self._data()
        self.assertAlmostEqual(
            posted_data['revenue_collection'] - before['revenue_collection'], 0.0, places=2)
        self.assertAlmostEqual(
            posted_data['revenue_invoice'] - before['revenue_invoice'], amount, places=2)
        self.assertNotIn(order, Order.search([('id', '=', order.id)] + posted_data['order_revenue_domain']))
