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


class TestAccountMove(TransactionCase):
    """Test cases for account.move model inherited in complete_insurance_system.

    Verifies that the custom fields (commission_id, insurance_id, claim_id)
    added to account.move are correctly stored and retrievable.
    """

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Insurance Partner',
        })
        # Minimal insurance policy prerequisites
        self.category = self.env['insurance.policy.category'].create({
            'name': 'Health', 'code': 'HLT',
        })
        self.sub_category = self.env['insurance.policy.sub.category'].create({
            'name': 'Individual Health', 'category_id': self.category.id,
        })
        self.insured_doc = self.env['insured.document'].create(
            {'name': 'Aadhaar Card'})
        self.claim_doc = self.env['claim.document'].create(
            {'name': 'Hospital Bill'})
        self.policy = self.env['insurance.policy'].create({
            'insurance_policy_id': self.sub_category.id,
            'policy_number': 'POL-001',
            'insurance_amount': 100000.0,
            'claim_amount': 50000.0,
            'policy_document_ids': [(4, self.insured_doc.id)],
            'claim_document_ids': [(4, self.claim_doc.id)],
        })
        self.insurance = self.env['res.insurance'].create({
            'policy_holder_id': self.partner.id,
            'gender': 'male',
            'insurance_policy_id': self.policy.id,
            'commission_type': 'fixed',
            'payment_type': 'fixed',
        })
        self.claim_reason = self.env['claim.reason'].create(
            {'name': 'Accident'})
        self.claim = self.env['insurance.claim'].create({
            'insurance_id': self.insurance.id,
            'claim_reason_id': self.claim_reason.id,
        })

    def test_account_move_has_commission_id_field(self):
        """account.move must have the custom commission_id field."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'commission_id': self.insurance.id,
        })
        self.assertEqual(move.commission_id.id, self.insurance.id,
                         "commission_id should be linked to the insurance record.")

    def test_account_move_has_insurance_id_field(self):
        """account.move must have the custom insurance_id (readonly) field."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'insurance_id': self.insurance.id,
        })
        self.assertEqual(move.insurance_id.id, self.insurance.id,
                         "insurance_id should be linked to the insurance record.")

    def test_account_move_has_claim_id_field(self):
        """account.move must have the custom claim_id field."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'claim_id': self.claim.id,
        })
        self.assertEqual(move.claim_id.id, self.claim.id,
                         "claim_id should be linked to the insurance claim.")

    def test_account_move_insurance_fields_default_empty(self):
        """Custom insurance fields must default to empty/False on a plain invoice."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertFalse(move.commission_id,
                         "commission_id should be empty by default.")
        self.assertFalse(move.insurance_id,
                         "insurance_id should be empty by default.")
        self.assertFalse(move.claim_id,
                         "claim_id should be empty by default.")