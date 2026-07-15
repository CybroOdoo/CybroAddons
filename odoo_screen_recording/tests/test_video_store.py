# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha AP (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestVideoStore(TransactionCase):

    def setUp(self):
        super().setUp()
        self.VideoStore = self.env['video.store']

    def test_01_create_video_store_record(self):
        record = self.VideoStore.create({
            'description': 'Test Screen Recording',
            'video': 'https://example.com/test_video.webm',
        })
        self.assertTrue(record.id, "VideoStore record should be created with a valid ID.")
        self.assertEqual(record.description, 'Test Screen Recording')
        self.assertEqual(record.video, 'https://example.com/test_video.webm')

    def test_02_date_default_populated(self):
        record = self.VideoStore.create({
            'description': 'Auto Date Test',
            'video': 'https://example.com/auto_date.webm',
        })
        self.assertIsNotNone(record.date, "Date field should be auto-populated on record creation.")

    def test_03_video_record_method_creates_entry(self):
        initial_count = self.VideoStore.search_count([])
        self.VideoStore.video_record('https://example.com/recorded.webm')
        new_count = self.VideoStore.search_count([])
        self.assertEqual(new_count, initial_count + 1, "video_record() should create exactly one new record.")

    def test_04_video_record_method_stores_url(self):
        url = 'https://example.com/my_recording.webm'
        self.VideoStore.video_record(url)
        record = self.VideoStore.search([('video', '=', url)], limit=1)
        self.assertTrue(record, "The record created by video_record() should be findable by URL.")
        self.assertEqual(record.video, url)

    def test_05_video_record_method_returns_true(self):
        result = self.VideoStore.video_record('https://example.com/return_check.webm')
        self.assertTrue(result, "video_record() method should return True upon successful record creation.")

    def test_06_video_record_description_is_empty_string(self):
        url = 'https://example.com/desc_check.webm'
        self.VideoStore.video_record(url)
        record = self.VideoStore.search([('video', '=', url)], limit=1)
        self.assertTrue(record, "Record should exist after video_record() call.")
        self.assertEqual(record.description, '', "Description set by video_record() should be an empty string.")

    def test_07_update_description(self):
        record = self.VideoStore.create({
            'description': 'Initial Description',
            'video': 'https://example.com/update_test.webm',
        })
        record.write({'description': 'Updated Description'})
        self.assertEqual(record.description, 'Updated Description', "Description should be updatable via write().")

    def test_08_update_video_url(self):
        record = self.VideoStore.create({
            'description': 'URL Update Test',
            'video': 'https://example.com/old.webm',
        })
        new_url = 'https://example.com/new.webm'
        record.write({'video': new_url})
        self.assertEqual(record.video, new_url, "Video URL should be updatable via write().")

    def test_09_delete_video_store_record(self):
        record = self.VideoStore.create({
            'description': 'Delete Test',
            'video': 'https://example.com/delete.webm',
        })
        record_id = record.id
        record.unlink()
        remaining = self.VideoStore.search([('id', '=', record_id)])
        self.assertFalse(remaining, "Record should be deleted and not found after unlink().")

    def test_10_search_by_description(self):
        self.VideoStore.create({
            'description': 'UniqueSearchDesc',
            'video': 'https://example.com/search.webm',
        })
        results = self.VideoStore.search([('description', '=', 'UniqueSearchDesc')])
        self.assertTrue(results, "Search by description should return at least one matching record.")

    def test_11_rec_name_is_date(self):
        self.assertEqual(
            self.VideoStore._rec_name,
            'date',
            "The _rec_name of video.store should be 'date'."
        )

    def test_12_multiple_video_records_created(self):
        urls = [
            'https://example.com/video1.webm',
            'https://example.com/video2.webm',
            'https://example.com/video3.webm',
        ]
        initial_count = self.VideoStore.search_count([])
        for url in urls:
            self.VideoStore.video_record(url)
        final_count = self.VideoStore.search_count([])
        self.assertEqual(
            final_count,
            initial_count + len(urls),
            "Each call to video_record() should create exactly one record."
        )
