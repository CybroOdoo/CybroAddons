# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from datetime import date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

class TestResInsurance(TransactionCase):
    """Test cases for the res.insurance model (main insurance policy record).
     """

    # ------------------------------------------------------------------
    # Shared test data
    # ------------------------------------------------------------------

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create(
            {'name': 'Policy Holder A'})
        self.agent_partner = self.env['res.partner'].create(
            {'name': 'Agent X', 'agent': True})
        self.category = self.env['insurance.policy.category'].create(
            {'name': 'Health', 'code': 'HLT'})
        self.sub_category = self.env['insurance.policy.sub.category'].create(
            {'name': 'Family Floater', 'category_id': self.category.id})
        self.insured_doc = self.env['insured.document'].create(
            {'name': 'ID Proof'})
        self.claim_doc = self.env['claim.document'].create(
            {'name': 'Discharge Summary'})
        self.policy = self.env['insurance.policy'].create({
            'insurance_policy_id': self.sub_category.id,
            'policy_number': 'POL-HLT-001',
            'insurance_amount': 300000.0,
            'claim_amount': 100000.0,
            'policy_document_ids': [(4, self.insured_doc.id)],
            'claim_document_ids': [(4, self.claim_doc.id)],
        })

    def _make_insurance(self, **kwargs):
        """Helper: create a res.insurance with sensible defaults."""
        vals = {
            'policy_holder_id': self.partner.id,
            'gender': 'male',
            'insurance_policy_id': self.policy.id,
            'commission_type': 'fixed',
            'payment_type': 'fixed',
        }
        vals.update(kwargs)
        return self.env['res.insurance'].create(vals)

    # ------------------------------------------------------------------
    # Creation & sequence
    # ------------------------------------------------------------------

    def test_insurance_created_with_sequence_number(self):
        """A newly created res.insurance must have a sequence number (not 'New')."""
        ins = self._make_insurance()
        self.assertTrue(ins.insurance_no,
                        "insurance_no should be populated after creation.")
        self.assertNotEqual(ins.insurance_no, 'New',
                            "insurance_no must not remain 'New'.")


    def test_insurance_default_state_is_new(self):
        """A new insurance record must have state 'new'."""
        ins = self._make_insurance()
        self.assertEqual(ins.state, 'new',
                         "Default state should be 'new'.")


    def test_insurance_required_policy_holder(self):
        """Creating insurance without policy_holder_id must raise an error."""
        with self.assertRaises(Exception):
            self._make_insurance(policy_holder_id=False)


    def test_insurance_required_gender(self):
        """Creating insurance without gender must raise an error."""
        with self.assertRaises(Exception):
            self._make_insurance(gender=False)


    # ------------------------------------------------------------------
    # _compute_age
    # ------------------------------------------------------------------

    def test_compute_age_valid_dob(self):
        """Age must be computed correctly from a valid date of birth."""
        dob = date.today() - timedelta(days=365 * 30)
        ins = self._make_insurance(dob=dob)
        self.assertGreaterEqual(ins.age, 29,
                                "Age should be approximately 30 years.")


    def test_compute_age_no_dob_returns_zero(self):
        """Age must default to 0 when dob is not set."""
        ins = self._make_insurance()
        self.assertEqual(ins.age, 0, "Age should be 0 when dob is not set.")


    def test_compute_age_future_dob_raises_validation_error(self):
        """Setting a future dob must raise a ValidationError."""
        future_dob = date.today() + timedelta(days=365)
        ins = self._make_insurance()
        with self.assertRaises(ValidationError):
            ins.write({'dob': future_dob})
            # Force recomputation in case it's deferred
            ins._compute_age()


    # ------------------------------------------------------------------
    # _compute_commission_amount
    # ------------------------------------------------------------------

    def test_commission_amount_with_percentage(self):
        """percentage_amount must be correctly computed from policy amount and percentage."""
        ins = self._make_insurance(
            commission_type='percentage',
            commission_percentage=10,
        )
        expected = ins.policy_amount * (10 / 100)
        self.assertAlmostEqual(
            ins.percentage_amount, expected, places=2,
            msg="Commission amount should be 10% of policy amount.")


    def test_commission_amount_zero_percentage_equals_policy_amount(self):
        """When commission_percentage is 0, percentage_amount should equal policy_amount."""
        ins = self._make_insurance(
            commission_type='percentage',
            commission_percentage=0,
        )
        self.assertAlmostEqual(
            ins.percentage_amount, ins.policy_amount, places=2,
            msg="With 0%, percentage_amount should equal policy_amount.")


    # ------------------------------------------------------------------
    # _compute_installment_amount
    # ------------------------------------------------------------------

    def test_installment_amount_computed_correctly(self):
        """Installment amount must equal total_policy_amount / policy_duration."""
        ins = self._make_insurance(
            payment_type='installment', policy_duration=12)
        expected = ins.total_policy_amount / 12
        self.assertAlmostEqual(ins.amount_installment, expected, places=2,
                               msg="Installment amount must be total / duration.")


    def test_installment_amount_zero_when_no_duration(self):
        """Installment amount must be 0 when policy_duration is 0."""
        ins = self._make_insurance(
            payment_type='installment', policy_duration=0)
        self.assertEqual(ins.amount_installment, 0.0,
                         "Installment amount should be 0 when duration is 0.")


    # ------------------------------------------------------------------
    # _compute_amount_remaining
    # ------------------------------------------------------------------

    def test_amount_remaining_before_invoice(self):
        """Before any invoice, remaining amount should equal total_policy_amount."""
        ins = self._make_insurance()
        self.assertAlmostEqual(
            ins.amount_remaining, ins.total_policy_amount, places=2,
            msg="Remaining amount before invoice should equal total policy amount.")


    # ------------------------------------------------------------------
    # count_genders
    # ------------------------------------------------------------------

    def test_count_genders_returns_dict(self):
        """count_genders must return a dict with 'products' and 'count' keys."""
        ins = self._make_insurance()
        result = ins.count_genders()
        self.assertIn('products', result)
        self.assertIn('count', result)
        self.assertEqual(result['products'], ['Male', 'Female'])


    def test_count_genders_increments_male_count(self):
        """Creating a male insurance record must increment male count."""
        ins = self._make_insurance(gender='male')
        result = ins.count_genders()
        # Male count is at index 0
        self.assertGreaterEqual(result['count'][0], 1,
                                "Male count should be at least 1.")


    # ------------------------------------------------------------------
    # insurance_policy_count
    # ------------------------------------------------------------------

    def test_insurance_policy_count_returns_dict(self):
        """insurance_policy_count must return a dict with 'products' and 'count' keys."""
        ins = self._make_insurance()
        result = ins.insurance_policy_count()
        self.assertIn('products', result)
        self.assertIn('count', result)


    # ------------------------------------------------------------------
    # get_dashboard_data
    # ------------------------------------------------------------------

    def test_get_dashboard_data_keys(self):
        """get_dashboard_data must return all expected dashboard keys."""
        ins = self._make_insurance()
        data = ins.get_dashboard_data()
        expected_keys = [
            'total_insurance', 'new_insurance', 'running_insurance',
            'expired_insurance', 'total_claim', 'submitted_claim',
            'approved_claim', 'rejected_claim', 'agent_count',
            'categories_count', 'sub_categories_count', 'insurance_policy',
        ]
        for key in expected_keys:
            self.assertIn(key, data,
                          f"Dashboard data must contain '{key}'.")


    def test_get_dashboard_data_counts_are_non_negative(self):
        """All dashboard counts must be non-negative integers."""
        ins = self._make_insurance()
        data = ins.get_dashboard_data()
        for key, value in data.items():
            self.assertGreaterEqual(value, 0,
                                    f"Dashboard count '{key}' must be >= 0.")


    # ------------------------------------------------------------------
    # action_confirm_policy
    # ------------------------------------------------------------------

    def test_action_confirm_policy_without_missing_docs(self):
        """action_confirm_policy must set state to 'confirmed' when no docs required."""
        ins = self._make_insurance()
        ins.action_confirm_policy()
        self.assertEqual(ins.state, 'confirmed',
                         "State should be 'confirmed' after confirmation.")
        self.assertTrue(ins.issue_date,
                        "issue_date should be set after confirmation.")


    def test_action_confirm_policy_with_missing_attachment_raises_error(self):
        """action_confirm_policy must raise UserError when a doc has no attachment."""
        ins = self._make_insurance()
        # Add an insurance document without an attachment
        self.env['insurance.document'].create({
            'insurance_id': ins.id,
            'document_type': 'ID Proof',
            'document_attachment_id': False,
        })
        with self.assertRaises(UserError):
            ins.action_confirm_policy()


    # ------------------------------------------------------------------
    # action_create_claim
    # ------------------------------------------------------------------

    def test_action_create_claim_returns_action(self):
        """action_create_claim must return a valid window action dict."""
        ins = self._make_insurance()
        action = ins.action_create_claim()
        self.assertEqual(action.get('type'), 'ir.actions.act_window',
                         "Returned type must be 'ir.actions.act_window'.")
        self.assertEqual(action.get('res_model'), 'insurance.claim',
                         "Res model must be 'insurance.claim'.")
        self.assertEqual(
            action.get('context', {}).get('default_insurance_id'), ins.id,
            "Context must include default_insurance_id set to current record id.")


    # ------------------------------------------------------------------
    # action_insurance_expired
    # ------------------------------------------------------------------

    def test_action_insurance_expired_sets_state(self):
        """action_insurance_expired must set state to 'expired'."""
        ins = self._make_insurance()
        ins.action_insurance_expired()
        self.assertEqual(ins.state, 'expired',
                         "State should be 'expired'.")
        self.assertTrue(ins.expiry_date,
                        "expiry_date should be set.")


    # ------------------------------------------------------------------
    # action_commission_invoice
    # ------------------------------------------------------------------

    def test_action_commission_invoice_without_agent_raises_error(self):
        """action_commission_invoice must raise UserError when no agent is assigned."""
        ins = self._make_insurance()
        with self.assertRaises(UserError):
            ins.action_commission_invoice()


    def test_action_commission_invoice_with_agent_creates_invoice(self):
        """action_commission_invoice must create an invoice and return an action."""
        ins = self._make_insurance(
            agent_required=True,
            agent_id=self.agent_partner.id,
            commission_type='fixed',
            fixed_amount=5000.0,
        )
        action = ins.action_commission_invoice()
        self.assertTrue(ins.commission_invoice_id,
                        "commission_invoice_id should be set.")
        self.assertTrue(ins.is_invoice,
                        "is_invoice should be True after commission invoice creation.")
        self.assertEqual(action.get('res_model'), 'account.move',
                         "Action res_model must be 'account.move'.")


    # ------------------------------------------------------------------
    # action_create_fixed_invoice
    # ------------------------------------------------------------------

    def test_action_create_fixed_invoice(self):
        """action_create_fixed_invoice must create an invoice and set state to 'running'."""
        ins = self._make_insurance(payment_type='fixed')
        action = ins.action_create_fixed_invoice()
        self.assertEqual(ins.state, 'running',
                         "State should be 'running' after fixed invoice creation.")
        self.assertTrue(ins.fixed_invoice_id,
                        "fixed_invoice_id should be set.")
        self.assertTrue(ins.is_invoice,
                        "is_invoice should be True.")
        self.assertEqual(action.get('res_model'), 'account.move',
                         "Action res_model must be 'account.move'.")


    # ------------------------------------------------------------------
    # action_create_installment_invoice
    # ------------------------------------------------------------------

    def test_action_create_installment_invoice_no_duration_raises_error(self):
        """action_create_installment_invoice must raise ValidationError when duration is 0."""
        ins = self._make_insurance(payment_type='installment', policy_duration=0)
        with self.assertRaises(ValidationError):
            ins.action_create_installment_invoice()


    def test_action_create_installment_invoice_creates_invoice(self):
        """action_create_installment_invoice must create an invoice and set state."""
        ins = self._make_insurance(
            payment_type='installment', policy_duration=6)
        ins.action_create_installment_invoice()
        self.assertEqual(ins.state, 'running',
                         "State should be 'running' after installment invoice creation.")
        self.assertTrue(ins.invoice_ids,
                        "Invoice should be linked after installment invoice creation.")


    def test_action_create_installment_invoice_completed_raises_error(self):
        """Creating a new installment invoice when remaining amount <= 0 must raise error."""
        ins = self._make_insurance(
            payment_type='installment', policy_duration=1)
        ins.action_create_installment_invoice()
        # Force remaining to 0 by paying the invoice
        ins.invoice_ids.write({'amount_residual': 0})
        # Simulate remaining = 0 scenario
        ins.write({'invoice_ids': [(4, inv.id) for inv in ins.invoice_ids]})
        # Patch: write a very large invoice total so remaining becomes <= 0
        ins.invoice_ids[0].write({'amount_total': ins.total_policy_amount})
        with self.assertRaises(ValidationError):
            ins.action_create_installment_invoice()


    # ------------------------------------------------------------------
    # action_view_fixed_invoice / action_view_commission_invoice
    # ------------------------------------------------------------------

    def test_action_view_fixed_invoice_returns_action(self):
        """action_view_fixed_invoice must return a valid window action."""
        ins = self._make_insurance(payment_type='fixed')
        ins.action_create_fixed_invoice()
        action = ins.action_view_fixed_invoice()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertEqual(action.get('res_id'), ins.fixed_invoice_id.id)


    def test_action_view_commission_invoice_returns_action(self):
        """action_view_commission_invoice must return a valid window action."""
        ins = self._make_insurance(
            agent_required=True,
            agent_id=self.agent_partner.id,
            commission_type='fixed',
            fixed_amount=3000.0,
        )
        ins.action_commission_invoice()
        action = ins.action_view_commission_invoice()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertEqual(action.get('res_id'), ins.commission_invoice_id.id)

    # ------------------------------------------------------------------
    # _compute_invoice_count / _compute_insurance_fixed_invoice_count
    # ------------------------------------------------------------------

    def test_compute_invoice_count_starts_zero(self):
        """invoice_count must be 0 before creating any commission invoice."""
        ins = self._make_insurance()
        self.assertEqual(ins.invoice_count, 0)


    def test_compute_invoice_count_after_commission_invoice(self):
        """invoice_count must be 1 after creating a commission invoice."""
        ins = self._make_insurance(
            agent_required=True,
            agent_id=self.agent_partner.id,
            commission_type='fixed',
            fixed_amount=2000.0,
        )
        ins.action_commission_invoice()
        self.assertEqual(ins.invoice_count, 1)


    def test_compute_insurance_fixed_invoice_count_starts_zero(self):
        """insurance_fixed_invoice_count must be 0 before fixed invoice creation."""
        ins = self._make_insurance()
        self.assertEqual(ins.insurance_fixed_invoice_count, 0)

    def test_compute_insurance_fixed_invoice_count_after_fixed_invoice(self):
        """insurance_fixed_invoice_count must be 1 after fixed invoice creation."""
        ins = self._make_insurance(payment_type='fixed')
        ins.action_create_fixed_invoice()
        self.assertEqual(ins.insurance_fixed_invoice_count, 1)


class TestInsuranceNomineeDetails(TransactionCase):
    """Test cases for InsuranceNomineeDetails — age computation."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create(
            {'name': 'Nominee Holder'})
        category = self.env['insurance.policy.category'].create(
            {'name': 'NomCat', 'code': 'NOM'})
        sub = self.env['insurance.policy.sub.category'].create(
            {'name': 'NomSub', 'category_id': category.id})
        i_doc = self.env['insured.document'].create({'name': 'NomDoc'})
        c_doc = self.env['claim.document'].create({'name': 'NomClaimDoc'})
        policy = self.env['insurance.policy'].create({
            'insurance_policy_id': sub.id,
            'policy_number': 'POL-NOM-001',
            'insurance_amount': 50000.0,
            'claim_amount': 25000.0,
            'policy_document_ids': [(4, i_doc.id)],
            'claim_document_ids': [(4, c_doc.id)],
        })
        self.insurance = self.env['res.insurance'].create({
            'policy_holder_id': self.partner.id,
            'gender': 'female',
            'insurance_policy_id': policy.id,
            'commission_type': 'fixed',
            'payment_type': 'fixed',
        })

    def test_nominee_age_computed_from_dob(self):
        """Nominee age must be computed correctly from date of birth."""
        dob = date.today() - timedelta(days=365 * 25)
        nominee = self.env['insurance.nominee.details'].create({
            'nominee_detail_id': self.insurance.id,
            'dob': dob,
            'percentage': 100,
        })
        self.assertGreaterEqual(nominee.age, 24,
                                "Nominee age should be approximately 25.")


    def test_nominee_age_defaults_to_zero_without_dob(self):
        """Nominee age must be 0 when dob is not set."""
        nominee = self.env['insurance.nominee.details'].create({
            'nominee_detail_id': self.insurance.id,
            'percentage': 100,
        })
        self.assertEqual(nominee.age, 0,
                         "Nominee age should be 0 when dob is not set.")

