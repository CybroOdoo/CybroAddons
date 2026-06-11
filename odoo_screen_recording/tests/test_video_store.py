# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import common



class TestVideoStore(common.TransactionCase):

    def setUp(self):
        super(TestVideoStore, self).setUp()
        self.VideoStore = self.env['video.store']

    def test_video_record(self):
        """Test the creation of a screen record video record via video_record function"""
        test_url = 'https://example.com/recording.webm'
        
        # Initially, there shouldn't be any records with this url
        initial_records = self.VideoStore.search([('video', '=', test_url)])
        self.assertFalse(initial_records)

        # Call video_record
        res = self.VideoStore.video_record(test_url)
        self.assertTrue(res)

        # Retrieve and verify the record
        record = self.VideoStore.search([('video', '=', test_url)])
        self.assertEqual(len(record), 1)
        self.assertEqual(record.video, test_url)
        self.assertEqual(record.description, '')
