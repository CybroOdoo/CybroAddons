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
from odoo.tests.common import TransactionCase

class TestInsurancePolicy(TransactionCase):
    """Test cases for the insurance.policy model.

    Covers:
    - Record creation and required field validation
    - Related field (policy_category_id via sub-category)
    - Many2many document assignments
    - Monetary fields (insurance_amount, claim_amount)
    - CRUD operations
    """

    def setUp(self):
        super().setUp()
        self.category = self.env['insurance.policy.category'].create(
            {'name': 'Motor', 'code': 'MOT'})
        self.sub_category = self.env['insurance.policy.sub.category'].create(
            {'name': 'Two-Wheeler', 'category_id': self.category.id})
        self.insured_doc = self.env['insured.document'].create(
            {'name': 'Vehicle RC'})
        self.claim_doc = self.env['claim.document'].create(
            {'name': 'Repair Bill'})

    def _make_policy(self, **kwargs):
        """Helper: create an insurance.policy with sensible defaults."""
        vals = {
            'insurance_policy_id': self.sub_category.id,
            'policy_number': 'POL-TEST-001',
            'insurance_amount': 75000.0,
            'claim_amount': 30000.0,
            'policy_document_ids': [(4, self.insured_doc.id)],
            'claim_document_ids': [(4, self.claim_doc.id)],
        }
        vals.update(kwargs)
        return self.env['insurance.policy'].create(vals)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_create_insurance_policy(self):
        """An insurance policy must be creatable with all required fields."""
        policy = self._make_policy()
        self.assertTrue(policy.id,
                        "Insurance policy should be created successfully.")


    def test_policy_category_computed_from_sub_category(self):
        """policy_category_id must be computed from the linked sub-category."""
        policy = self._make_policy()
        self.assertEqual(policy.policy_category_id.id, self.category.id,
                         "policy_category_id must match the sub-category's parent category.")


    def test_insurance_amount_stored(self):
        """insurance_amount must be stored correctly."""
        policy = self._make_policy(insurance_amount=100000.0)
        self.assertEqual(policy.insurance_amount, 100000.0,
                         "insurance_amount should be 100000.0.")


    def test_claim_amount_stored(self):
        """claim_amount must be stored correctly."""
        policy = self._make_policy(claim_amount=40000.0)
        self.assertEqual(policy.claim_amount, 40000.0,
                         "claim_amount should be 40000.0.")


    # ------------------------------------------------------------------
    # Document relations
    # ------------------------------------------------------------------

    def test_policy_document_ids_linked(self):
        """policy_document_ids must include the assigned insured document."""
        policy = self._make_policy()
        self.assertIn(self.insured_doc, policy.policy_document_ids,
                      "Insured document must be linked to policy_document_ids.")


    def test_claim_document_ids_linked(self):
        """claim_document_ids must include the assigned claim document."""
        policy = self._make_policy()
        self.assertIn(self.claim_doc, policy.claim_document_ids,
                      "Claim document must be linked to claim_document_ids.")


    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    def test_policy_number_required(self):
        """Creating a policy without policy_number must raise an error."""
        with self.assertRaises(Exception):
            self._make_policy(policy_number=False)


    def test_insurance_policy_id_required(self):
        """Creating a policy without insurance_policy_id must raise an error."""
        with self.assertRaises(Exception):
            self._make_policy(insurance_policy_id=False)


    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def test_policy_update(self):
        """Insurance policy fields must be updatable."""
        policy = self._make_policy(policy_number='POL-OLD')
        policy.write({'policy_number': 'POL-NEW'})
        self.assertEqual(policy.policy_number, 'POL-NEW',
                         "policy_number should be updated.")


    def test_policy_delete(self):
        """An insurance policy must be deletable."""
        policy = self._make_policy(policy_number='POL-DEL')
        policy_id = policy.id
        policy.unlink()
        self.assertFalse(
            self.env['insurance.policy'].search([('id', '=', policy_id)]),
            "Insurance policy should be deleted.")


    def test_policy_currency_default(self):
        """Currency must default to the company currency."""
        policy = self._make_policy()
        self.assertEqual(policy.currency_id.id,
                         self.env.company.currency_id.id,
                         "Default currency must match the company currency.")

