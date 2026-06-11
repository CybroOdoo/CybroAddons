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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWhatsappMessage(TransactionCase):
    """Test cases for the survey.whatsapp.message model."""

    def test_whatsapp_message_creation(self):
        """A survey.whatsapp.message record must be creatable with all
        required fields and must persist to the database."""
        user = self.env.user
        message = self.env['whatsapp.message'].create({
            'status': 'sent',
            'from_user': user.id,
            'to_user': '9999999999',
            'body': 'Survey link sent',
        })

        self.assertTrue(message.exists(),
                        "The created record must exist in the database.")
        self.assertEqual(message.status, 'sent')
        self.assertEqual(message.from_user, user)
        self.assertEqual(message.to_user, '9999999999')
        self.assertEqual(message.body, 'Survey link sent')

    def test_whatsapp_message_default_status(self):
        """Verify that a message record created without an explicit status
        falls back to the model default (if any) without raising an error."""
        user = self.env.user
        message = self.env['whatsapp.message'].create({
            'from_user': user.id,
            'to_user': '8888888888',
            'body': 'Test message',
        })
        self.assertTrue(message.exists())

    def test_whatsapp_message_fields_are_readable(self):
        """All stored fields must be readable back from the recordset
        without raising an AccessError or missing attribute."""
        user = self.env.user
        message = self.env['whatsapp.message'].create({
            'status': 'sent',
            'from_user': user.id,
            'to_user': '7777777777',
            'body': 'Readable test',
        })
        message_db = self.env['whatsapp.message'].browse(message.id)
        self.assertEqual(message_db.body, 'Readable test')
        self.assertEqual(message_db.to_user, '7777777777')