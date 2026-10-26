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
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMobileComplaintTree(TransactionCase):
    """Test suite for mobile.complaint.tree model (mobile_complaint_tree.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Complaint Tree Customer'})
        cls.brand = cls.env['mobile.brand'].create({'brand_name': 'Asus'})
        cls.model = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand.id,
            'mobile_brand_models': 'ROG Phone 8',
        })
        cls.service = cls.env['mobile.service'].create({
            'person_name': cls.customer.id,
            'brand_name': cls.brand.id,
            'model_name': cls.model.id,
            'return_date': fields.Date.today() + timedelta(days=3),
        })

    def test_01_create_complaint_tree_line(self):
        """Test creating a complaint tree line linked to a service."""
        c_type = self.env['mobile.complaint'].create({'complaint_type': 'Speaker Issue'})
        c_desc = self.env['mobile.complaint.description'].create({
            'complaint_type_template': c_type.id,
            'description': 'Distorted audio during phone calls',
        })

        line = self.env['mobile.complaint.tree'].create({
            'complaint_id': self.service.id,
            'complaint_type_tree': c_type.id,
            'description_tree': c_desc.id,
        })
        self.assertEqual(line.complaint_id.id, self.service.id)
        self.assertEqual(line.complaint_type_tree.id, c_type.id)
        self.assertEqual(line.description_tree.id, c_desc.id)
        self.assertIn(line.id, self.service.complaints_tree.ids)

    def test_02_multiple_complaints_on_service(self):
        """Test attaching multiple complaints to the same mobile service."""
        c_type_screen = self.env['mobile.complaint'].create({'complaint_type': 'Cracked Screen'})
        c_desc_screen = self.env['mobile.complaint.description'].create({
            'complaint_type_template': c_type_screen.id,
            'description': 'Display broken on lower right corner',
        })

        c_type_port = self.env['mobile.complaint'].create({'complaint_type': 'USB Port'})
        c_desc_port = self.env['mobile.complaint.description'].create({
            'complaint_type_template': c_type_port.id,
            'description': 'Loose Type-C port, does not charge',
        })

        self.env['mobile.complaint.tree'].create({
            'complaint_id': self.service.id,
            'complaint_type_tree': c_type_screen.id,
            'description_tree': c_desc_screen.id,
        })
        self.env['mobile.complaint.tree'].create({
            'complaint_id': self.service.id,
            'complaint_type_tree': c_type_port.id,
            'description_tree': c_desc_port.id,
        })

        self.assertGreaterEqual(len(self.service.complaints_tree), 2)
        types = self.service.complaints_tree.mapped('complaint_type_tree.complaint_type')
        self.assertIn('Cracked Screen', types)
        self.assertIn('USB Port', types)
