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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestBillingRunCoverage(TransactionCase):
    """Monthly billing run constraints, guards, wizards and release of billed links."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Run Coverage Customer', 'billing_mode': 'monthly_run', 'email': 'cov@example.com'})

    def _run(self, **kw):
        vals = {'period_start': self.today.replace(day=1), 'period_end': self.today}
        vals.update(kw)
        return self.env['wm.monthly.billing.run'].create(vals)

    def test_period_constraint_and_sequence(self):
        run = self._run()
        self.assertNotEqual(run.name, 'New')
        with self.assertRaises(ValidationError):
            self._run(period_end=self.today - timedelta(days=60))

    def test_write_resets_done_run_to_draft(self):
        run = self._run()
        run.state = 'done'
        run.error_message = 'note'
        self.assertEqual(run.state, 'done')
        run.period_end = self.today + timedelta(days=1)
        self.assertEqual(run.state, 'draft')

    def test_done_run_cannot_be_deleted(self):
        run = self._run()
        run.state = 'done'
        with self.assertRaises(UserError):
            run.unlink()
        draft = self._run()
        draft.unlink()
        self.assertFalse(draft.exists())

    def test_run_billing_requires_billing_role(self):
        run = self._run()
        user = new_test_user(self.env, login='run_cov_plain', groups='base.group_user')
        with self.assertRaises(UserError):
            run.with_user(user).action_run_billing()

    def test_done_run_cannot_run_again(self):
        run = self._run()
        run.state = 'done'
        with self.assertRaises(UserError):
            run.action_run_billing()

    def test_run_without_orders_creates_no_invoice(self):
        run = self._run(partner_ids=[(6, 0, self.partner.ids)])
        run.action_run_billing()
        self.assertFalse(run.invoice_ids)
        self.assertEqual(run.invoice_count, 0)

    def test_view_invoices_action(self):
        run = self._run()
        action = run.action_view_invoices()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(action['domain'], [('id', 'in', [])])

    def test_wizard_period_validation_and_run(self):
        Wizard = self.env['wm.monthly.billing.wizard']
        bad = Wizard.create({
            'period_start': self.today, 'period_end': self.today - timedelta(days=3)})
        with self.assertRaises(UserError):
            bad.action_run_monthly_billing()
        good = Wizard.create({
            'period_start': self.today.replace(day=1), 'period_end': self.today,
            'partner_ids': [(6, 0, self.partner.ids)]})
        action = good.action_run_monthly_billing()
        run = self.env['wm.monthly.billing.run'].browse(action['res_id'])
        self.assertEqual(run.partner_ids, self.partner)
        self.assertEqual(run.period_start, self.today.replace(day=1))

    def test_release_billing_links_on_invoice_cancel(self):
        point = self.env['wm.collection.point'].create({'name': 'Run Cov Site', 'partner_id': self.partner.id})
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': point.id, 'state': 'completed'})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id})
        run = self._run()
        line = self.env['wm.monthly.billing.run.line'].create({
            'run_id': run.id, 'partner_id': self.partner.id, 'invoice_id': invoice.id,
            'collection_order_ids': [(6, 0, order.ids)], 'state': 'billed'})
        order.billing_run_line_id = line
        invoice._release_billing_links(invoice)
        self.assertEqual(line.state, 'draft')
        self.assertFalse(order.billing_run_line_id)
        self.assertIn('released', line.note)
        # Direct invoice link is released as well
        order2 = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': point.id, 'state': 'completed'})
        order2.direct_invoice_id = invoice
        invoice._release_billing_links(invoice)
        self.assertFalse(order2.direct_invoice_id)

    def test_release_noop_for_non_cancelled(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id})
        invoice._release_billing_links()  # draft: nothing to release, no error

    def test_reject_wizard_requires_submitted_request(self):
        point = self.env['wm.collection.point'].create({'name': 'Rej Site', 'partner_id': self.partner.id})
        req = self.env['wm.portal.service.request'].create({
            'partner_id': self.partner.id, 'collection_point_id': point.id,
            'request_type': 'container_swap', 'requested_date': self.today})
        req.state = 'submitted'
        wiz = self.env['wm.portal.request.reject.wizard'].create({'request_id': req.id, 'reason': 'No'})
        self.assertEqual(wiz.action_reject(), {'type': 'ir.actions.act_window_close'})
        self.assertEqual(req.state, 'rejected')
        self.assertEqual(req.rejection_reason, 'No')

    def test_sla_email_wizard_errors(self):
        sla = self.env['wm.sla'].create({'name': 'Wiz SLA', 'terms_and_conditions': 'T'})
        partner = self.env['res.partner'].create({'name': 'No Email Customer'})
        contract = self.env['wm.partner.contract'].create({
            'partner_id': partner.id, 'sla_id': sla.id,
            'from_date': self.today, 'to_date': self.today + timedelta(days=30),
            'frequency': 'monthly', 'no_of_frequency': 1, 'billing_basis': 'per_collection',
            'fixed_price': 1.0, 'max_weight': 1.0, 'overweight_price': 1.0})
        wiz = self.env['wm.sla.send.email.wizard'].create({
            'sla_id': sla.id, 'contract_id': contract.id, 'reason': 'Late pickup'})
        sla.breach_template_id = False
        with self.assertRaises(ValidationError):
            wiz.action_send_email()
        sla.breach_template_id = self.env['mail.template'].create({
            'name': 'Cov Breach', 'model_id': self.env['ir.model']._get('wm.partner.contract').id,
            'subject': 'Breach', 'body_html': '<p>x</p>'})
        with self.assertRaises(ValidationError):
            wiz.action_send_email()  # customer has no email
