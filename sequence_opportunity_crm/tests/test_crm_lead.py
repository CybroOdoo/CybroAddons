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
from odoo.tests import TransactionCase, tagged
from odoo.addons.sequence_opportunity_crm import assign_missing_opportunity_codes_post_init


@tagged('post_install', '-at_install')
class TestCrmLead(TransactionCase):
    """Test cases for 'crm.lead' model in sequence_opportunity_crm."""

    def test_create(self):
        """Test create automatically assigns opportunity_code from sequence."""
        # 1. Single lead creation without opportunity_code
        lead_1 = self.env['crm.lead'].create({
            'name': 'Test Opportunity 1',
            'type': 'opportunity',
        })
        self.assertTrue(lead_1.opportunity_code)
        self.assertTrue(lead_1.opportunity_code.startswith('OPPO'))
        # 2. Multi-lead batch creation
        leads = self.env['crm.lead'].create([
            {'name': 'Test Opportunity 2', 'type': 'opportunity'},
            {'name': 'Test Opportunity 3', 'type': 'opportunity'},
        ])
        for lead in leads:
            self.assertTrue(lead.opportunity_code)
            self.assertTrue(lead.opportunity_code.startswith('OPPO'))
        self.assertNotEqual(leads[0].opportunity_code, leads[1].opportunity_code)
        # 3. Lead created with pre-existing opportunity_code is preserved
        lead_custom = self.env['crm.lead'].create({
            'name': 'Test Opportunity Custom',
            'type': 'opportunity',
            'opportunity_code': 'CUSTOM_CODE_123',
        })
        self.assertEqual(lead_custom.opportunity_code, 'CUSTOM_CODE_123')

    def test__assign_missing_opportunity_codes(self):
        """Test _assign_missing_opportunity_codes populates codes for records without one."""
        # Create records and reset opportunity_code to False to simulate existing legacy records
        lead_active = self.env['crm.lead'].create({'name': 'Legacy Active Lead'})
        lead_inactive = self.env['crm.lead'].create({'name': 'Legacy Inactive Lead', 'active': False})
        lead_active.opportunity_code = False
        lead_inactive.opportunity_code = False
        self.assertFalse(lead_active.opportunity_code)
        self.assertFalse(lead_inactive.opportunity_code)
        # Run _assign_missing_opportunity_codes
        self.env['crm.lead']._assign_missing_opportunity_codes()
        self.assertTrue(lead_active.opportunity_code)
        self.assertTrue(lead_active.opportunity_code.startswith('OPPO'))
        self.assertTrue(lead_inactive.opportunity_code)
        self.assertTrue(lead_inactive.opportunity_code.startswith('OPPO'))
        self.assertNotEqual(lead_active.opportunity_code, lead_inactive.opportunity_code)
    test_assign_missing_opportunity_codes = test__assign_missing_opportunity_codes

    def test_assign_missing_opportunity_codes_post_init(self):
        """Test post_init_hook assigns codes to existing records."""
        lead = self.env['crm.lead'].create({'name': 'Legacy Post Init Lead'})
        lead.opportunity_code = False
        self.assertFalse(lead.opportunity_code)
        assign_missing_opportunity_codes_post_init(self.env)
        self.assertTrue(lead.opportunity_code)
        self.assertTrue(lead.opportunity_code.startswith('OPPO'))
