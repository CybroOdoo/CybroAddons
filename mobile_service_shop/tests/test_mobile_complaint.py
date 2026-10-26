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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMobileComplaint(TransactionCase):
    """Test suite for mobile.complaint model (mobile_complaint.py)."""

    def test_01_create_complaint_type(self):
        """Test creating a complaint type and verifying display_name."""
        complaint = self.env['mobile.complaint'].create({
            'complaint_type': 'Overheating Issue',
        })
        self.assertEqual(complaint.complaint_type, 'Overheating Issue')
        self.assertEqual(complaint.display_name, 'Overheating Issue')

    def test_02_multiple_complaints_listing(self):
        """Test listing multiple complaint types."""
        c1 = self.env['mobile.complaint'].create({'complaint_type': 'Microphone Glitch'})
        c2 = self.env['mobile.complaint'].create({'complaint_type': 'No SIM Detected'})
        types = self.env['mobile.complaint'].search([('id', 'in', [c1.id, c2.id])])
        self.assertEqual(len(types), 2)
        self.assertIn('Microphone Glitch', types.mapped('complaint_type'))
        self.assertIn('No SIM Detected', types.mapped('complaint_type'))
