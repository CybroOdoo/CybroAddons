# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'progress_billing')
class TestProgressBillingAnalyticAccount(TransactionCase):
    """Tests for the AccountAnalyticAccount model extension."""

    def setUp(self):
        super().setUp()
        # Create a basic analytic plan (required in Odoo 17+)
        self.analytic_plan = self.env['account.analytic.plan'].search(
            [], limit=1
        )
        if not self.analytic_plan:
            self.analytic_plan = self.env['account.analytic.plan'].create({
                'name': 'Test Plan',
            })

    def test_01_total_progress_billing_default_zero(self):
        """total_progress_billing defaults to 0.0 on a new analytic account."""
        analytic = self.env['account.analytic.account'].create({
            'name': 'Test Project Alpha',
            'plan_id': self.analytic_plan.id,
        })
        self.assertEqual(
            analytic.total_progress_billing, 0.0,
            "Default total_progress_billing should be 0.0"
        )

    def test_02_total_progress_billing_set_positive(self):
        """total_progress_billing can be set to a positive float."""
        analytic = self.env['account.analytic.account'].create({
            'name': 'Test Project Beta',
            'plan_id': self.analytic_plan.id,
            'total_progress_billing': 50000.0,
        })
        self.assertAlmostEqual(
            analytic.total_progress_billing, 50000.0,
            msg="total_progress_billing should store 50000.0"
        )

    def test_03_total_progress_billing_update(self):
        """total_progress_billing can be updated after creation."""
        analytic = self.env['account.analytic.account'].create({
            'name': 'Test Project Gamma',
            'plan_id': self.analytic_plan.id,
            'total_progress_billing': 10000.0,
        })
        analytic.write({'total_progress_billing': 75000.0})
        self.assertAlmostEqual(
            analytic.total_progress_billing, 75000.0,
            msg="total_progress_billing should be updated to 75000.0"
        )

    def test_04_total_progress_billing_zero_value(self):
        """total_progress_billing can be explicitly set to 0."""
        analytic = self.env['account.analytic.account'].create({
            'name': 'Test Project Delta',
            'plan_id': self.analytic_plan.id,
            'total_progress_billing': 5000.0,
        })
        analytic.write({'total_progress_billing': 0.0})
        self.assertAlmostEqual(
            analytic.total_progress_billing, 0.0,
            msg="total_progress_billing should be reset to 0.0"
        )


@tagged('post_install', '-at_install', 'progress_billing')
class TestProgressBillingAccountMove(TransactionCase):
    """Tests for the AccountMove model extension."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Analytic plan
        cls.analytic_plan = cls.env['account.analytic.plan'].search(
            [], limit=1
        )
        if not cls.analytic_plan:
            cls.analytic_plan = cls.env['account.analytic.plan'].create({
                'name': 'Default Plan',
            })

        # Analytic account (project)
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Construction Project 2026',
            'plan_id': cls.analytic_plan.id,
            'total_progress_billing': 100000.0,
        })

        # Partner (customer)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'customer_rank': 1,
        })

        # Company currency
        cls.currency = cls.env.company.currency_id

        # Income account for invoice lines
        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not cls.account_income:
            cls.account_income = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'TEST_INC_001',
                'account_type': 'income',
            })

        # Journal

        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)


    # Helper – create a draft customer invoice
    def _create_invoice(self, amount, project=None, title=None):
        """Return a draft out_invoice for the test partner."""
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Service Line',
                'quantity': 1,
                'price_unit': amount,
                'account_id': self.account_income.id,
            })],
        }
        if project:
            invoice_vals['project_id'] = project.id
        if title:
            invoice_vals['progress_bill_title'] = title
        return self.env['account.move'].create(invoice_vals)


    # 1. Field: progress_bill_title
    def test_05_progress_bill_title_default_empty(self):
        """progress_bill_title defaults to False/empty on a new invoice."""
        invoice = self._create_invoice(1000.0)
        self.assertFalse(
            invoice.progress_bill_title,
            "progress_bill_title should be empty by default"
        )

    def test_06_progress_bill_title_can_be_set(self):
        """progress_bill_title stores a string value correctly."""
        invoice = self._create_invoice(
            2000.0, title='Phase 1 – Foundation Works'
        )
        self.assertEqual(
            invoice.progress_bill_title,
            'Phase 1 – Foundation Works',
            "progress_bill_title should match the assigned value"
        )

    def test_07_progress_bill_title_write(self):
        """progress_bill_title can be updated via write()."""
        invoice = self._create_invoice(1500.0, title='Initial Title')
        invoice.write({'progress_bill_title': 'Updated Title'})
        self.assertEqual(invoice.progress_bill_title, 'Updated Title')


    # 2. Field: project_id (Many2one)
    def test_08_project_id_default_empty(self):
        """project_id defaults to empty on a new invoice."""
        invoice = self._create_invoice(500.0)
        self.assertFalse(
            invoice.project_id,
            "project_id should be empty by default"
        )

    def test_09_project_id_can_be_set(self):
        """project_id can be linked to an analytic account."""
        invoice = self._create_invoice(
            5000.0, project=self.analytic_account
        )
        self.assertEqual(
            invoice.project_id, self.analytic_account,
            "project_id should reference the assigned analytic account"
        )


    # 3. Field: total_progress_billing (related from project_id)
    def test_10_total_progress_billing_related_no_project(self):
        """total_progress_billing is 0 when no project is linked."""
        invoice = self._create_invoice(3000.0)
        self.assertAlmostEqual(
            invoice.total_progress_billing, 0.0,
            msg="total_progress_billing must be 0 without a project"
        )

    def test_11_total_progress_billing_related_with_project(self):
        """total_progress_billing mirrors the analytic account value."""
        invoice = self._create_invoice(
            3000.0, project=self.analytic_account
        )
        self.assertAlmostEqual(
            invoice.total_progress_billing,
            self.analytic_account.total_progress_billing,
            msg="total_progress_billing should equal the project's value (100000)"
        )

    def test_12_total_progress_billing_reflects_analytic_update(self):
        """total_progress_billing updates when the analytic account changes."""
        invoice = self._create_invoice(
            3000.0, project=self.analytic_account
        )
        self.analytic_account.write({'total_progress_billing': 200000.0})
        invoice.invalidate_recordset()
        self.assertAlmostEqual(
            invoice.total_progress_billing, 200000.0,
            msg="total_progress_billing should reflect the updated analytic value"
        )
        # Restore for other tests
        self.analytic_account.write({'total_progress_billing': 100000.0})

    # 4. Method: _compute_current_invoice
    def test_13_compute_current_invoice_equals_amount_total(self):
        """current_invoice equals amount_total on a draft invoice."""
        invoice = self._create_invoice(8000.0)
        self.assertAlmostEqual(
            invoice.current_invoice, invoice.amount_total,
            msg="current_invoice should equal amount_total"
        )

    def test_14_compute_current_invoice_after_line_update(self):
        """current_invoice updates when invoice lines change."""
        invoice = self._create_invoice(8000.0)
        # Update price_unit on the existing line
        invoice.write({
            'invoice_line_ids': [(1, invoice.invoice_line_ids[0].id, {
                'price_unit': 12000.0,
            })]
        })
        self.assertAlmostEqual(
            invoice.current_invoice, invoice.amount_total,
            msg="current_invoice must stay in sync with amount_total"
        )

    # ------------------------------------------------------------------
    # 5. Method: _compute_less_paid_amount
    # ------------------------------------------------------------------
    def test_15_less_paid_amount_equals_amount_residual_draft(self):
        """less_paid_amount equals amount_residual on a draft invoice."""
        invoice = self._create_invoice(6000.0)
        self.assertAlmostEqual(
            invoice.less_paid_amount, invoice.amount_residual,
            msg="less_paid_amount should equal amount_residual"
        )

    def test_16_less_paid_amount_after_post(self):
        """less_paid_amount equals full amount after posting (no payment)."""
        invoice = self._create_invoice(
            6000.0, project=self.analytic_account
        )
        invoice.action_post()
        self.assertAlmostEqual(
            invoice.less_paid_amount, invoice.amount_residual,
            msg="less_paid_amount should equal amount_residual after posting"
        )


    # 6. Method: _compute_invoice_to_date (no prior posted invoices)
    def test_17_invoice_to_date_no_prior_invoices(self):
        """invoice_to_date is 0 when this is the first posted invoice."""
        invoice = self._create_invoice(
            10000.0, project=self.analytic_account
        )
        invoice.action_post()
        self.assertAlmostEqual(
            invoice.invoice_to_date, 0.0,
            msg="invoice_to_date should be 0 with no prior invoices"
        )

    def test_18_invoice_to_date_with_prior_posted_invoice(self):
        """invoice_to_date accumulates posted invoices for the same project."""
        # First posted invoice for the project
        inv1 = self._create_invoice(
            20000.0, project=self.analytic_account
        )
        inv1.action_post()

        # Second invoice – invoice_to_date should reflect inv1
        inv2 = self._create_invoice(
            15000.0, project=self.analytic_account
        )
        inv2.action_post()
        inv2.invalidate_recordset()

        self.assertAlmostEqual(
            inv2.invoice_to_date, inv1.amount_total,
            msg="invoice_to_date should equal the total of prior posted invoices"
        )

    def test_19_invoice_to_date_no_project(self):
        """invoice_to_date is 0 when no project is set."""
        invoice = self._create_invoice(5000.0)
        invoice.action_post()
        self.assertAlmostEqual(
            invoice.invoice_to_date, 0.0,
            msg="invoice_to_date must be 0 when project_id is not set"
        )


    # 7. Method: _compute_remaining_progress_billing
    def test_20_remaining_progress_billing_no_prior_invoices(self):
        """remaining = total_progress_billing when invoice_to_date is 0."""
        invoice = self._create_invoice(
            5000.0, project=self.analytic_account
        )
        invoice.action_post()
        expected = self.analytic_account.total_progress_billing  # 100000
        self.assertAlmostEqual(
            invoice.remaining_progress_billing, expected,
            msg="remaining_progress_billing should equal total when no prior invoices"
        )

    def test_21_remaining_progress_billing_with_prior_invoices(self):
        """remaining decreases as prior invoices accumulate."""
        inv1 = self._create_invoice(
            30000.0, project=self.analytic_account
        )
        inv1.action_post()

        inv2 = self._create_invoice(
            20000.0, project=self.analytic_account
        )
        inv2.action_post()
        inv2.invalidate_recordset()

        expected = (
            self.analytic_account.total_progress_billing
            - inv2.invoice_to_date
        )
        self.assertAlmostEqual(
            inv2.remaining_progress_billing, expected,
            msg="remaining_progress_billing should be total minus invoice_to_date"
        )

    def test_22_remaining_progress_billing_no_project(self):
        """remaining_progress_billing is 0 without a project."""
        invoice = self._create_invoice(5000.0)
        invoice.action_post()
        self.assertAlmostEqual(
            invoice.remaining_progress_billing, 0.0,
            msg="remaining_progress_billing must be 0 without a project"
        )


    # 8. Method: _compute_previously_invoiced
    def test_23_previously_invoice_single_invoice(self):
        """previously_invoice is 0 when this is the only invoice."""
        invoice = self._create_invoice(
            25000.0, project=self.analytic_account
        )
        invoice.action_post()
        invoice.invalidate_recordset()
        self.assertAlmostEqual(
            invoice.previously_invoice, 0.0,
            msg="previously_invoice should be 0 for the sole posted invoice"
        )

    def test_24_previously_invoice_multiple_invoices(self):
        """previously_invoice accumulates amounts from prior invoices."""
        inv1 = self._create_invoice(
            15000.0, project=self.analytic_account
        )
        inv1.action_post()

        inv2 = self._create_invoice(
            10000.0, project=self.analytic_account
        )
        inv2.action_post()
        inv2.invalidate_recordset()

        # previously_invoice on inv2 should include inv1's amount_total
        self.assertAlmostEqual(
            inv2.previously_invoice, inv1.amount_total,
            msg="previously_invoice should equal sum of prior invoices"
        )

    def test_25_previously_invoice_no_project(self):
        """previously_invoice is 0 when no project is linked."""
        invoice = self._create_invoice(8000.0)
        invoice.action_post()
        self.assertAlmostEqual(
            invoice.previously_invoice, 0.0,
            msg="previously_invoice must be 0 without a project"
        )


    # 9. Method: _compute_total_due

    def test_26_total_due_single_invoice_no_payment(self):
        """total_due = previously_invoice_due + less_paid_amount."""
        invoice = self._create_invoice(
            12000.0, project=self.analytic_account
        )
        invoice.action_post()
        expected = invoice.previously_invoice_due + invoice.less_paid_amount
        self.assertAlmostEqual(
            invoice.total_due, expected,
            msg="total_due should equal previously_invoice_due + less_paid_amount"
        )

    def test_27_total_due_two_invoices(self):
        """total_due on the second invoice accounts for prior residual."""
        inv1 = self._create_invoice(
            20000.0, project=self.analytic_account
        )
        inv1.action_post()

        inv2 = self._create_invoice(
            10000.0, project=self.analytic_account
        )
        inv2.action_post()
        inv2.invalidate_recordset()

        expected = inv2.previously_invoice_due + inv2.less_paid_amount
        self.assertAlmostEqual(
            inv2.total_due, expected,
            msg="total_due should equal previously_invoice_due + less_paid_amount"
        )

    def test_28_total_due_no_project(self):
        """total_due equals less_paid_amount when no project is set."""
        invoice = self._create_invoice(7000.0)
        invoice.action_post()
        # previously_invoice_due = 0, total_due = 0 + amount_residual
        self.assertAlmostEqual(
            invoice.total_due, invoice.amount_residual,
            msg="total_due should equal amount_residual when no project is set"
        )


    # 10. Integration – full progress billing workflow

    def test_29_full_progress_billing_workflow(self):
        """
        End-to-end: three invoices against the same project.

        Invoice 1 (20 000) → posted
        Invoice 2 (30 000) → posted
        Invoice 3 (10 000) → checked for all progress-billing fields
        """
        project = self.env['account.analytic.account'].create({
            'name': 'E2E Project',
            'plan_id': self.analytic_plan.id,
            'total_progress_billing': 100000.0,
        })

        inv1 = self._create_invoice(20000.0, project=project)
        inv1.action_post()

        inv2 = self._create_invoice(30000.0, project=project)
        inv2.action_post()

        inv3 = self._create_invoice(10000.0, project=project)
        inv3.action_post()
        inv3.invalidate_recordset()

        # total_progress_billing
        self.assertAlmostEqual(inv3.total_progress_billing, 100000.0)

        # invoice_to_date = inv1 + inv2 amounts
        expected_itd = inv1.amount_total + inv2.amount_total
        self.assertAlmostEqual(inv3.invoice_to_date, expected_itd)

        # remaining = 100000 - invoice_to_date
        self.assertAlmostEqual(
            inv3.remaining_progress_billing,
            100000.0 - expected_itd
        )

        # current_invoice = inv3.amount_total
        self.assertAlmostEqual(inv3.current_invoice, inv3.amount_total)

        # total_due = previously_invoice_due + less_paid_amount
        self.assertAlmostEqual(
            inv3.total_due,
            inv3.previously_invoice_due + inv3.less_paid_amount
        )

    def test_30_progress_bill_title_not_copied_on_duplicate(self):
        """progress_bill_title has copy=False — duplicate clears the title."""
        invoice = self._create_invoice(
            5000.0,
            project=self.analytic_account,
            title='Phase 1 Billing'
        )
        copy_inv = invoice.copy()
        self.assertFalse(
            copy_inv.progress_bill_title,
            "progress_bill_title should not be copied (copy=False)"
        )

    def test_31_project_id_not_copied_on_duplicate(self):
        """project_id has copy=False — duplicate should have no project."""
        invoice = self._create_invoice(
            5000.0, project=self.analytic_account
        )
        copy_inv = invoice.copy()
        self.assertFalse(
            copy_inv.project_id,
            "project_id should not be copied (copy=False)"
        )

    def test_32_invoice_to_date_excludes_draft_invoices(self):
        """invoice_to_date only counts *posted* invoices, not drafts."""
        # Posted invoice
        inv_posted = self._create_invoice(
            40000.0, project=self.analytic_account
        )
        inv_posted.action_post()

        # Draft invoice (not posted) – should NOT count
        inv_draft = self._create_invoice(
            25000.0, project=self.analytic_account
        )

        # Another posted invoice – invoice_to_date should only see inv_posted
        inv_check = self._create_invoice(
            10000.0, project=self.analytic_account
        )
        inv_check.action_post()
        inv_check.invalidate_recordset()

        self.assertAlmostEqual(
            inv_check.invoice_to_date, inv_posted.amount_total,
            msg="invoice_to_date must exclude draft invoices"
        )
        # Keep the draft alive to avoid teardown issues
        _ = inv_draft
