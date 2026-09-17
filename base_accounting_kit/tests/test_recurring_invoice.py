# -*- coding: utf-8 -*-
from freezegun import freeze_time
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestRecurringInvoice(AccountKitCommon):

    def _template(self, **kw):
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'interval_number': 1,
            'interval_type': 'months',
            'date_start': '2020-01-01',
            'line_ids': [Command.create({
                'product_id': self.product_a.id,
                'name': 'Monthly service',
                'quantity': 2.0,
                'price_unit': 100.0,
            })],
        }
        vals.update(kw)
        return self.env['account.recurring.invoice'].create(vals)

    @freeze_time('2020-03-15')
    def test_generates_due_invoices_and_advances_schedule(self):
        """Running monthly template generates one invoice per due period."""
        tmpl = self._template()
        tmpl.action_start()
        self.assertEqual(tmpl.date_next.isoformat(), '2020-01-01')
        self.env['account.recurring.invoice']._cron_generate_invoices()
        # Jan, Feb, Mar are due at 2020-03-15.
        self.assertEqual(tmpl.invoice_count, 3)
        self.assertEqual(tmpl.date_next.isoformat(), '2020-04-01',
                         "Schedule advances past the last generated period")
        inv = tmpl.invoice_ids[0]
        self.assertEqual(inv.move_type, 'out_invoice')
        self.assertEqual(inv.partner_id, self.partner_a)
        self.assertEqual(inv.recurring_invoice_id, tmpl)
        self.assertAlmostEqual(inv.amount_untaxed, 200.0, 2)

    @freeze_time('2020-03-15')
    def test_auto_post_toggle(self):
        """auto_post posts the invoices; otherwise they stay draft."""
        draft_tmpl = self._template()
        draft_tmpl.action_start()
        draft_tmpl._generate_due()
        self.assertEqual(set(draft_tmpl.invoice_ids.mapped('state')), {'draft'})

        posted_tmpl = self._template(auto_post=True)
        posted_tmpl.action_start()
        posted_tmpl._generate_due()
        self.assertEqual(set(posted_tmpl.invoice_ids.mapped('state')),
                         {'posted'})

    @freeze_time('2020-06-01')
    def test_end_date_closes_template(self):
        """Generation stops at date_end and the template becomes Done."""
        tmpl = self._template(date_end='2020-02-15')
        tmpl.action_start()
        tmpl._generate_due()
        self.assertEqual(tmpl.invoice_count, 2, "Only Jan and Feb are in range")
        self.assertEqual(tmpl.state, 'done')

    def test_start_requires_lines(self):
        """A template with no lines cannot be started."""
        tmpl = self._template(line_ids=[])
        with self.assertRaises(UserError):
            tmpl.action_start()

    @freeze_time('2020-03-15')
    def test_vendor_bill_template(self):
        """The template also drives vendor bills."""
        tmpl = self._template(move_type='in_invoice',
                              partner_id=self.partner_b.id)
        tmpl.action_start()
        tmpl._generate_due()
        self.assertTrue(tmpl.invoice_ids)
        self.assertEqual(set(tmpl.invoice_ids.mapped('move_type')),
                         {'in_invoice'})

    @freeze_time('2020-01-01')
    def test_generate_now_without_due_raises(self):
        """Generate Now on a template with nothing due reports it clearly."""
        tmpl = self._template(date_start='2020-02-01')
        tmpl.action_start()
        with self.assertRaises(UserError):
            tmpl.action_generate_now()

    def test_name_sequence_assigned(self):
        """Templates get a RECINV/ reference from the global sequence."""
        tmpl = self._template()
        self.assertTrue(tmpl.name.startswith('RECINV/'))
