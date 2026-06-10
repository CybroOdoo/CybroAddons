# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
#############################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCrmLead(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.crm_lead_model = cls.env['crm.lead']

    def test_create_lead_generates_opportunity_code(self):
        """Test that opportunity_code is automatically generated upon crm.lead creation."""
        lead = self.crm_lead_model.create({
            'name': 'New Testing Opportunity',
            'type': 'opportunity',
        })
        self.assertTrue(lead.opportunity_code)
        self.assertIsInstance(lead.opportunity_code, str)

    def test_assign_missing_opportunity_codes(self):
        """Test _assign_missing_opportunity_codes correctly assigns codes to records without it."""
        lead = self.crm_lead_model.create({
            'name': 'Existing Opportunity Without Code',
            'type': 'opportunity',
        })
        lead.write({'opportunity_code': False})
        self.assertFalse(lead.opportunity_code)
        self.crm_lead_model._assign_missing_opportunity_codes()
        lead.invalidate_recordset()
        self.assertTrue(lead.opportunity_code)
