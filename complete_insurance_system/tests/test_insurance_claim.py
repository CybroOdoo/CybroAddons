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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestInsuranceClaim(TransactionCase):
    """Test cases for the insurance.claim model.

    Covers:
    - Record creation with auto sequence
    - State machine transitions (draft → submitted → approved / rejected)
    - action_submit validation (missing document attachments)
    - action_claim_settlement_amount invoice creation
    - action_view_claim_invoice action return
    - _compute_invoice_count
    """

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create(
            {'name': 'Claim Test Partner'})
        self.category = self.env['insurance.policy.category'].create(
            {'name': 'Life', 'code': 'LIF'})
        self.sub_category = self.env['insurance.policy.sub.category'].create(
            {'name': 'Term Life', 'category_id': self.category.id})
        self.insured_doc = self.env['insured.document'].create(
            {'name': 'PAN Card'})
        self.claim_doc_type = self.env['claim.document'].create(
            {'name': 'Death Certificate'})
        self.policy = self.env['insurance.policy'].create({
            'insurance_policy_id': self.sub_category.id,
            'policy_number': 'POL-LIFE-001',
            'insurance_amount': 500000.0,
            'claim_amount': 200000.0,
            'policy_document_ids': [(4, self.insured_doc.id)],
            'claim_document_ids': [(4, self.claim_doc_type.id)],
        })
        self.insurance = self.env['res.insurance'].create({
            'policy_holder_id': self.partner.id,
            'gender': 'female',
            'insurance_policy_id': self.policy.id,
            'commission_type': 'fixed',
            'payment_type': 'fixed',
        })
        self.claim_reason = self.env['claim.reason'].create(
            {'name': 'Critical Illness'})

    def _make_claim(self):
        """Helper: create a fresh insurance claim."""
        return self.env['insurance.claim'].create({
            'insurance_id': self.insurance.id,
            'claim_reason_id': self.claim_reason.id,
        })

    # ------------------------------------------------------------------
    # Creation & sequence
    # ------------------------------------------------------------------

    def test_claim_created_with_sequence_number(self):
        """A newly created claim must have a sequence number (not 'New')."""
        claim = self._make_claim()
        self.assertTrue(claim.claim_no,
                        "claim_no should be set after creation.")
        self.assertNotEqual(claim.claim_no, 'New',
                            "claim_no should not remain 'New' after creation.")


    def test_claim_default_state_is_draft(self):
        """A newly created claim must have state 'draft'."""
        claim = self._make_claim()
        self.assertEqual(claim.state, 'draft',
                         "Default state for a new claim should be 'draft'.")


    def test_claim_related_fields_from_insurance(self):
        """Claim must inherit related fields from the linked insurance record."""
        claim = self._make_claim()
        self.assertEqual(claim.policy_holder_id.id,
                         self.insurance.policy_holder_id.id,
                         "policy_holder_id should be inherited from insurance.")
        self.assertEqual(claim.gender, self.insurance.gender,
                         "gender should be inherited from insurance.")


    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def test_action_submit_without_documents_raises_error(self):
        """action_submit must raise UserError when claim documents lack attachments."""
        claim = self._make_claim()
        # Manually add a claim document line without an attachment
        self.env['insurance.claim.document'].create({
            'claim_id': claim.id,
            'document_type': 'Medical Report',
            'document_attachment_id': False,
        })
        with self.assertRaises(UserError):
            claim.action_submit()


    def test_action_submit_without_missing_docs_moves_to_submitted(self):
        """action_submit with all docs attached should set state to 'submitted'."""
        claim = self._make_claim()
        # No documents required — claim should move to submitted
        claim.action_submit()
        self.assertEqual(claim.state, 'submitted',
                         "Claim state should be 'submitted' after action_submit.")


    def test_action_approved_sets_state(self):
        """action_approved must change claim state to 'approved'."""
        claim = self._make_claim()
        claim.action_submit()
        claim.action_approved()
        self.assertEqual(claim.state, 'approved',
                         "Claim state should be 'approved'.")


    def test_action_rejected_sets_state(self):
        """action_rejected must change claim state to 'rejected'."""
        claim = self._make_claim()
        claim.action_submit()
        claim.action_rejected()
        self.assertEqual(claim.state, 'rejected',
                         "Claim state should be 'rejected'.")


    # ------------------------------------------------------------------
    # Invoice creation
    # ------------------------------------------------------------------

    def test_action_claim_settlement_amount_creates_invoice(self):
        """action_claim_settlement_amount must create an account.move invoice."""
        claim = self._make_claim()
        claim.action_claim_settlement_amount()
        self.assertTrue(claim.invoice_id,
                        "Invoice should be created after claim settlement.")
        self.assertEqual(claim.invoice_id.move_type, 'in_invoice',
                         "Settlement invoice must be a vendor bill (in_invoice).")


    def test_action_claim_settlement_amount_no_duplicate_invoice(self):
        """Calling action_claim_settlement_amount twice must not create a second invoice."""
        claim = self._make_claim()
        claim.action_claim_settlement_amount()
        first_invoice_id = claim.invoice_id.id
        claim.action_claim_settlement_amount()
        self.assertEqual(claim.invoice_id.id, first_invoice_id,
                         "A second call must not replace the existing invoice.")


    def test_compute_invoice_count(self):
        """_compute_invoice_count should return 1 after an invoice is created."""
        claim = self._make_claim()
        self.assertEqual(claim.invoice_count, 0,
                         "invoice_count should start at 0.")
        claim.action_claim_settlement_amount()
        self.assertEqual(claim.invoice_count, 1,
                         "invoice_count should be 1 after invoice creation.")


    def test_action_view_claim_invoice_returns_action(self):
        """action_view_claim_invoice must return a valid window action dict."""
        claim = self._make_claim()
        claim.action_claim_settlement_amount()
        action = claim.action_view_claim_invoice()
        self.assertEqual(action.get('type'), 'ir.actions.act_window',
                         "Returned action type must be 'ir.actions.act_window'.")
        self.assertEqual(action.get('res_model'), 'account.move',
                         "Returned action res_model must be 'account.move'.")
        self.assertEqual(action.get('res_id'), claim.invoice_id.id,
                         "Action res_id must match the claim invoice id.")

