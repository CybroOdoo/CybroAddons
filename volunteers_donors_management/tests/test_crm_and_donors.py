# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCrmAndDonors(TransactionCase):
    """Test cases for CRM lead, donor, and partner features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.donor_type = cls.env['donor.type'].create({
            'donor_type': 'Individual Donor',
            'donor_code': 'DON_IND_01',
            'description': '<p>Regular individual donor</p>',
        })
        cls.volunteer_type = cls.env['volunteer.type'].create({
            'volunteer_type': 'Community Volunteer',
            'volunteer_code': 'VOL_COMM_01',
            'description': '<p>Local community volunteer</p>',
        })
        cls.volunteer_skill = cls.env['volunteer.skill'].create({
            'volunteer_skill': 'First Aid',
            'volunteer_skill_code': 'FA_01',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Supporter',
            'email': 'supporter@example.com',
            'is_volunteer': True,
            'is_donor': True,
            'donor_type_id': cls.donor_type.id,
            'volunteer_type_id': cls.volunteer_type.id,
            'volunteer_skill_ids': [Command.link(cls.volunteer_skill.id)],
        })

    def test_partner_volunteer_and_donor_data(self):
        """Verify partner volunteer and donor flags and relation fields."""
        self.assertTrue(self.partner.is_volunteer)
        self.assertTrue(self.partner.is_donor)
        self.assertEqual(self.partner.donor_type_id, self.donor_type)
        self.assertEqual(self.partner.volunteer_type_id, self.volunteer_type)
        self.assertIn(self.volunteer_skill, self.partner.volunteer_skill_ids)

    def test_crm_lead_volunteer_donor_fields(self):
        """Verify CRM lead related fields reflect partner volunteer and donor information."""
        lead = self.env['crm.lead'].create({
            'name': 'Donation Opportunity',
            'partner_id': self.partner.id,
        })
        self.assertEqual(lead.donor_type_id, self.donor_type)
        self.assertEqual(lead.volunteer_type_id, self.volunteer_type)
        self.assertIn(self.volunteer_skill, lead.volunteer_skill_ids)
