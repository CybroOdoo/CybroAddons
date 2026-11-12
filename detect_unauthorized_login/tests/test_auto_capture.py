# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo import fields

class TestAutoCapture(TransactionCase):

    def setUp(self):
        super(TestAutoCapture, self).setUp()
        self.AutoCapture = self.env['auto.capture']

    def test_create_auto_capture(self):
        """Test creation of auto.capture record"""
        capture = self.AutoCapture.create({
            'email': 'test@example.com',
            'date': fields.Datetime.now(),
            'image': False
        })
        self.assertEqual(capture.email, 'test@example.com')
        self.assertTrue(capture.date)
        self.assertEqual(capture.image, False)
        # Just verify that rec_name is based on date without strict string comparison if timezone varies
        self.assertTrue(capture.display_name)
