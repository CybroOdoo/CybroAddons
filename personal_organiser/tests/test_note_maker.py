# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Aleena K(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestNoteMaker(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref('base.user_admin')
        cls.note = cls.env['note.maker'].create({
            'note_title': 'Daily Reminder',
            'note': 'Complete Odoo Testing',
            'user_id': cls.user.id,
        })

    def test_note_creation(self):
        """Test note creation"""
        self.assertRecordValues(self.note, [{
            'note_title': 'Daily Reminder',
            'note': 'Complete Odoo Testing',
            'user_id': self.user.id,
        }])

    def test_note_update(self):
        """Test note update"""
        self.note.write({
            'note_title': 'Updated Reminder',
            'note': 'Updated Content',
        })
        self.assertRecordValues(self.note, [{
            'note_title': 'Updated Reminder',
            'note': 'Updated Content',
        }])

    def test_note_deletion(self):
        """Test note deletion"""
        note_id = self.note.id
        self.note.unlink()
        deleted_note = self.env['note.maker'].browse(note_id)
        self.assertFalse(
            deleted_note.exists(),
            "Note was not deleted properly"
        )
