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
class TestMobileComplaintDescription(TransactionCase):
    """Test suite for mobile.complaint.description model (mobile_complaint_description.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.complaint_type = cls.env['mobile.complaint'].create({
            'complaint_type': 'Camera Problem',
        })

    def test_01_create_complaint_description(self):
        """Test creating a complaint description template."""
        desc = self.env['mobile.complaint.description'].create({
            'complaint_type_template': self.complaint_type.id,
            'description': 'Rear camera blurry and unable to autofocus',
        })
        self.assertEqual(desc.complaint_type_template.id, self.complaint_type.id)
        self.assertEqual(desc.description, 'Rear camera blurry and unable to autofocus')
        self.assertEqual(desc.display_name, 'Rear camera blurry and unable to autofocus')

    def test_02_filter_descriptions_by_type(self):
        """Test filtering complaint descriptions by complaint type."""
        other_type = self.env['mobile.complaint'].create({'complaint_type': 'Bluetooth'})
        d1 = self.env['mobile.complaint.description'].create({
            'complaint_type_template': self.complaint_type.id,
            'description': 'Front camera black screen',
        })
        d2 = self.env['mobile.complaint.description'].create({
            'complaint_type_template': other_type.id,
            'description': 'Cannot pair with wireless earbuds',
        })

        cam_descs = self.env['mobile.complaint.description'].search([
            ('complaint_type_template', '=', self.complaint_type.id)
        ])
        self.assertIn(d1.id, cam_descs.ids)
        self.assertNotIn(d2.id, cam_descs.ids)
