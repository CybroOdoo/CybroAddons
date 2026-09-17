# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestBankReconcile(AccountKitCommon):

    def _statement_line(self, amount=-50.0):
        return self.env['account.bank.statement.line'].create({
            'journal_id': self.bank_journal.id,
            'payment_ref': 'Bank charge',
            'amount': amount,
            'date': '2020-01-01',
        })

    def test_new_statement_line_not_reconciled(self):
        """A fresh imported line sits on the suspense account, unreconciled."""
        st_line = self._statement_line()
        self.assertFalse(st_line.is_reconciled)
        self.assertEqual(st_line.bank_state, 'valid')

    def test_button_validation_assigns_counterpart_account(self):
        """Validating with a chosen account reconciles the line (assigns the
        counterpart, clearing the suspense line)."""
        st_line = self._statement_line()
        st_line.account_id = self.expense_account
        st_line.button_validation()
        self.assertTrue(st_line.is_reconciled,
                        "Assigning the counterpart account must reconcile the line")
        self.assertEqual(st_line.bank_state, 'reconciled')

    def test_button_validation_requires_a_selection(self):
        """Validating without an account or a matched entry raises."""
        st_line = self._statement_line()
        with self.assertRaises(UserError):
            st_line.button_validation()

    def test_button_reset_undoes_reconciliation(self):
        """Resetting a reconciled line restores the suspense counterpart."""
        st_line = self._statement_line()
        st_line.account_id = self.expense_account
        st_line.button_validation()
        self.assertTrue(st_line.is_reconciled)
        st_line.button_reset()
        self.assertFalse(st_line.is_reconciled)

    # --- auto-matching (Phase 3 #4) -------------------------------------
    def test_auto_reconcile_by_partner_and_amount(self):
        """A statement line auto-matches a unique open invoice of the same
        partner and amount, then reconciles."""
        self.init_invoice('out_invoice', partner=self.partner_a,
                          invoice_date='2020-01-01', amounts=[100.0],
                          taxes=[], post=True)
        st_line = self.env['account.bank.statement.line'].create({
            'journal_id': self.bank_journal.id,
            'payment_ref': 'Customer payment',
            'partner_id': self.partner_a.id,
            'amount': 100.0,
            'date': '2020-01-02',
        })
        proposal = st_line._get_reconcile_proposal()
        self.assertTrue(proposal.get('move_line'),
                        "A matching open invoice line is proposed")
        st_line._auto_reconcile()
        self.assertTrue(st_line.is_reconciled)

    def test_auto_reconcile_by_reconcile_model_rule(self):
        """A statement line matching a reconcile-model label rule is
        categorised to the rule's write-off account."""
        model = self.env['account.reconcile.model'].create({
            'name': 'Bank Fees',
            'company_id': self.env.company.id,
            'match_label': 'contains',
            'match_label_param': 'FEE',
            'line_ids': [(0, 0, {
                'account_id': self.expense_account.id,
                'amount_type': 'percentage',
                'amount_string': '100',
            })],
        })
        st_line = self.env['account.bank.statement.line'].create({
            'journal_id': self.bank_journal.id,
            'payment_ref': 'MONTHLY BANK FEE',
            'amount': -12.0,
            'date': '2020-01-02',
        })
        # The rule's label condition matches this line...
        self.assertTrue(st_line._reconcile_model_matches(model))
        # ...and a write-off account is proposed (the first matching rule wins).
        proposal = st_line._get_reconcile_proposal()
        self.assertTrue(proposal.get('account'),
                        "A reconcile-model write-off account is proposed")
        st_line._auto_reconcile()
        self.assertTrue(st_line.is_reconciled)

    def test_action_auto_reconcile_batch(self):
        """The batch action reconciles matchable lines."""
        self.init_invoice('out_invoice', partner=self.partner_a,
                          invoice_date='2020-01-01', amounts=[100.0],
                          taxes=[], post=True)
        st_line = self.env['account.bank.statement.line'].create({
            'journal_id': self.bank_journal.id,
            'payment_ref': 'Customer payment',
            'partner_id': self.partner_a.id,
            'amount': 100.0,
            'date': '2020-01-02',
        })
        st_line.action_auto_reconcile()
        self.assertTrue(st_line.is_reconciled)

    def test_auto_reconcile_cron_inactive(self):
        """The auto-reconcile cron ships disabled."""
        cron = self.env.ref('base_accounting_kit.ir_cron_bank_auto_reconcile')
        self.assertFalse(cron.active)

    # --- reconciliation widget entry point ------------------------------
    def test_action_open_reconcile_targets_widget_views(self):
        """The dashboard 'to Reconcile' button opens the statement-line
        kanban/list that hosts the reconciliation widget."""
        action = self.bank_journal.action_open_reconcile()
        self.assertEqual(action['res_model'], 'account.bank.statement.line')
        self.assertEqual(action['context']['default_journal_id'],
                         self.bank_journal.id)
        view_types = [vt for _vid, vt in action['views']]
        self.assertIn('kanban', view_types)
        # The kanban and the reconcile-widget form both resolve.
        self.env.ref(
            'base_accounting_kit.account_bank_statement_line_view_kanban')
        self.env.ref(
            'base_accounting_kit.view_bank_reconcile_widget_form')

    def test_statement_list_allows_manual_create(self):
        """The Bank Statements list re-enables New (base ships create=false)
        so statements can be built by hand."""
        view = self.env.ref('account.view_bank_statement_tree')
        arch = self.env['account.bank.statement'].get_view(
            view.id, 'list')['arch']
        self.assertIn('create="true"', arch,
                      "The statement list must allow manual creation")

    def test_manual_statement_with_lines_feeds_widget(self):
        """A statement built by hand (the form path) with lines produces an
        unreconciled statement line ready for the reconcile widget, and the
        statement journal derives from its lines."""
        stmt = self.env['account.bank.statement'].create({
            'name': 'Manual BNK',
            'line_ids': [(0, 0, {
                'date': '2020-01-03',
                'payment_ref': 'Manual receipt',
                'journal_id': self.bank_journal.id,
                'amount': 75.0,
            })],
        })
        self.assertEqual(stmt.journal_id, self.bank_journal,
                         "Statement journal derives from its lines")
        self.assertEqual(len(stmt.line_ids), 1)
        self.assertFalse(stmt.line_ids.is_reconciled)
        self.assertEqual(stmt.line_ids.bank_state, 'valid')
