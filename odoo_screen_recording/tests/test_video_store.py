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
"""Test suite for Screen Record Video Storage."""
import logging
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestVideoStore(TransactionCase):
    """Unit tests for video.store model and methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_video_data = "data:video/webm;base64,GkXfo59ChoEBQveBAULygQ8="
        cls.demo_user = cls.env['res.users'].create({
            'name': 'Test Screen Recording User',
            'login': 'test_screen_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_create_video_store_record(self):
        """Test creating a video.store record directly."""
        record = self.env['video.store'].create({
            'description': 'Test Recording Description',
            'video': self.test_video_data,
        })
        self.assertTrue(record.id, "Record should be successfully created.")
        self.assertEqual(record.description, 'Test Recording Description')
        self.assertEqual(record.video, self.test_video_data)
        self.assertTrue(record.date, "Date field should have a default value.")

    def test_video_record_method(self):
        """Test video_record API model method used by systray recording."""
        initial_count = self.env['video.store'].search_count([])
        result = self.env['video.store'].video_record(self.test_video_data)

        self.assertTrue(result, "video_record should return True on success.")
        new_count = self.env['video.store'].search_count([])
        self.assertEqual(new_count, initial_count + 1, "A new video.store record should be created.")

        latest_record = self.env['video.store'].search([], order='id desc', limit=1)
        self.assertEqual(latest_record.video, self.test_video_data)
        self.assertEqual(latest_record.description, '')

    def test_default_date_assignment(self):
        """Test that date is automatically assigned on creation."""
        now = fields.Datetime.now()
        record = self.env['video.store'].create({
            'description': 'Check Date',
            'video': 'data:video/webm;base64,AAA=',
        })
        self.assertIsNotNone(record.date)
        self.assertAlmostEqual(
            record.date.timestamp(),
            now.timestamp(),
            delta=60,
            msg="Date should default to approximately current time."
        )

    def test_access_rights_internal_user(self):
        """Test that internal users can create and read video.store records."""
        user_env = self.env['video.store'].with_user(self.demo_user)
        record = user_env.create({
            'description': 'User Recording',
            'video': self.test_video_data,
        })
        self.assertTrue(record.id, "Internal user should have permission to create video.store record.")

        read_record = user_env.browse(record.id)
        self.assertEqual(read_record.description, 'User Recording')

        read_record.write({'description': 'Updated User Recording'})
        self.assertEqual(read_record.description, 'Updated User Recording')

        read_record.unlink()
        self.assertFalse(read_record.exists(), "Internal user should have permission to unlink video.store record.")
