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


class TestResPartner(TransactionCase):
    """Test cases for the res.partner model as extended by complete_insurance_system.

    Covers:
    - The 'agent' Boolean field (default False)
    - The insurance_line_ids One2many relationship
    - The InsuranceDetails model fields
    """

    def setUp(self):
        super().setUp()
        self.category = self.env['insurance.policy.category'].create(
            {'name': 'PartnerCat', 'code': 'PRC'})

    # ------------------------------------------------------------------
    # agent field
    # ------------------------------------------------------------------

    def test_partner_agent_default_false(self):
        """The agent field must default to False on a new partner."""
        partner = self.env['res.partner'].create({'name': 'Regular Contact'})
        self.assertFalse(partner.agent,
                         "agent should default to False.")


    def test_partner_can_be_marked_as_agent(self):
        """A partner can be explicitly marked as an agent."""
        partner = self.env['res.partner'].create(
            {'name': 'Insurance Agent', 'agent': True})
        self.assertTrue(partner.agent,
                        "agent should be True when explicitly set.")


    def test_partner_agent_update(self):
        """The agent field must be updatable."""
        partner = self.env['res.partner'].create({'name': 'Contact B'})
        self.assertFalse(partner.agent)
        partner.write({'agent': True})
        self.assertTrue(partner.agent,
                        "agent field should be True after update.")


    def test_partner_agent_search(self):
        """Search by agent=True must return only agent partners."""
        self.env['res.partner'].create({'name': 'Agent Y', 'agent': True})
        agents = self.env['res.partner'].search([('agent', '=', True)])
        for ag in agents:
            self.assertTrue(ag.agent,
                            "All returned partners should have agent=True.")


    # ------------------------------------------------------------------
    # insurance_line_ids
    # ------------------------------------------------------------------

    def test_insurance_line_ids_initially_empty(self):
        """insurance_line_ids must be empty for a newly created partner."""
        partner = self.env['res.partner'].create({'name': 'Clean Partner'})
        self.assertFalse(partner.insurance_line_ids,
                         "insurance_line_ids should be empty initially.")


    def test_insurance_line_can_be_added(self):
        """An insurance detail line must be addable to a partner's insurance_line_ids."""
        partner = self.env['res.partner'].create(
            {'name': 'Insured Person'})
        self.env['insurance.details'].create({
            'insurance_detail_id': partner.id,
            'insurance_id': 'INS-001',
            'policy_holder_id': partner.id,
            'policy_category_id': self.category.id,
        })
        self.assertEqual(len(partner.insurance_line_ids), 1,
                         "One insurance detail should be linked to the partner.")


    # ------------------------------------------------------------------
    # InsuranceDetails model
    # ------------------------------------------------------------------

    def test_insurance_details_created(self):
        """An insurance.details record must be creatable with all fields."""
        partner = self.env['res.partner'].create({'name': 'Detail Owner'})
        detail = self.env['insurance.details'].create({
            'insurance_detail_id': partner.id,
            'insurance_id': 'INS-XYZ',
            'policy_holder_id': partner.id,
            'policy_category_id': self.category.id,
        })
        self.assertTrue(detail.id,
                        "InsuranceDetails record should be created.")
        self.assertEqual(detail.insurance_id, 'INS-XYZ')


    def test_insurance_details_dates(self):
        """issue_date and expiry_date must be stored correctly."""
        partner = self.env['res.partner'].create({'name': 'Date Owner'})
        detail = self.env['insurance.details'].create({
            'insurance_detail_id': partner.id,
            'insurance_id': 'INS-DATE',
            'issue_date': '2024-01-01',
            'expiry_date': '2025-01-01',
        })
        self.assertEqual(str(detail.issue_date), '2024-01-01')
        self.assertEqual(str(detail.expiry_date), '2025-01-01')


    def test_insurance_details_commission_bill_id(self):
        """commission_bill_id must store a string value."""
        partner = self.env['res.partner'].create({'name': 'Commission Owner'})
        detail = self.env['insurance.details'].create({
            'insurance_detail_id': partner.id,
            'insurance_id': 'INS-COMM',
            'commission_bill_id': 'INV/2024/001',
        })
        self.assertEqual(detail.commission_bill_id, 'INV/2024/001',
                         "commission_bill_id should be stored correctly.")

