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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for hr.employee face recognition extensions."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrEmployeeFaceRecognition(TransactionCase):
    """Test suite covering hr.employee face recognition field and POS data loading."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({'name': 'Test POS Config'})

        cls.sample_image = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC'
        )

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Face Cashier',
            'image': cls.sample_image,
        })

    def test_employee_face_image_field(self):
        """Test that the image field can be stored and retrieved on hr.employee."""
        self.assertTrue(self.employee.image, "Employee face image should be stored.")
        self.assertEqual(self.employee.image.to_base64(), self.sample_image)

    def test_load_pos_data_fields_includes_face_fields(self):
        """Test that _load_pos_data_fields includes image, image_1920, and avatar_512."""
        loaded_fields = self.env['hr.employee']._load_pos_data_fields(self.pos_config)
        self.assertIn('image', loaded_fields, "'image' field must be loaded for POS.")
        self.assertIn('image_1920', loaded_fields, "'image_1920' field must be loaded for POS.")
        self.assertIn('avatar_512', loaded_fields, "'avatar_512' field must be loaded for POS.")

    def test_load_pos_data_fields_preserves_base_fields(self):
        """Test that existing base fields are preserved when extending _load_pos_data_fields."""
        loaded_fields = self.env['hr.employee']._load_pos_data_fields(self.pos_config)
        self.assertIn('name', loaded_fields)
        self.assertIn('user_id', loaded_fields)
