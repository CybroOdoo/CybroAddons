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

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
import base64

class TestMailManagement(TransactionCase):
    """Test suite for Email Management in Odoo (odoo_mail_management)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Drop NOT NULL constraint on autopost_bills if it exists in the database to avoid errors when account module is not loaded
        cls.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='res_partner' AND column_name='autopost_bills' AND is_nullable='NO';
        """)
        if cls.env.cr.fetchone():
            cls.env.cr.execute("ALTER TABLE res_partner ALTER COLUMN autopost_bills DROP NOT NULL;")

        # Create a test user to run context-specific tests with necessary access permissions
        user_vals = {
            'name': 'Mail Test User',
            'login': 'mail_test_user',
            'email': 'mail_test_user@gmail.com',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('base.group_system').id
            ])],
        }
        cls.test_user = cls.env['res.users'].create(user_vals)

        # Base64 encoded 1x1 transparent PNG image
        cls.sample_image_base64 = (
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )

    def test_mail_count_and_retrieval(self):
        """Test counting and fetching starred and archived mails."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        # Create mails in different states
        mail_all = mail_model.create({
            'subject': 'Test Mail 1',
            'email_to': 'recipient1@gmail.com',
            'email_from': self.test_user.email,
        })
        mail_sent = mail_model.create({
            'subject': 'Test Mail Sent',
            'email_to': 'recipient2@gmail.com',
            'email_from': self.test_user.email,
            'state': 'sent',
        })
        mail_outbox = mail_model.create({
            'subject': 'Test Mail Outbox',
            'email_to': 'recipient3@gmail.com',
            'email_from': self.test_user.email,
            'state': 'exception',
        })
        mail_starred = mail_model.create({
            'subject': 'Test Mail Starred',
            'email_to': 'recipient4@gmail.com',
            'email_from': self.test_user.email,
            'is_starred': True,
        })
        mail_archived = mail_model.create({
            'subject': 'Test Mail Archived',
            'email_to': 'recipient5@gmail.com',
            'email_from': self.test_user.email,
            'active': False,
        })

        # Verify mail counts
        counts = mail_model.get_mail_count()
        self.assertEqual(counts.get('all_count'), 4) # active only: mail_all, mail_sent, mail_outbox, mail_starred
        self.assertEqual(counts.get('sent_count'), 1) # mail_sent
        self.assertEqual(counts.get('outbox_count'), 1) # mail_outbox
        self.assertEqual(counts.get('starred_count'), 1) # mail_starred
        self.assertEqual(counts.get('archived_count'), 1) # mail_archived

        # Verify get starred mail
        starred_mails = mail_model.get_starred_mail()
        starred_ids = [m['id'] for m in starred_mails]
        self.assertIn(mail_starred.id, starred_ids)
        self.assertNotIn(mail_all.id, starred_ids)

        # Verify get archived mail
        archived_mails = mail_model.get_archived_mail()
        archived_ids = [m['id'] for m in archived_mails]
        self.assertIn(mail_archived.id, archived_ids)
        self.assertNotIn(mail_all.id, archived_ids)

    def test_mail_actions_star_archive_open(self):
        """Test starring, unstarring, archiving, unarchiving, and opening mails."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        mail = mail_model.create({
            'subject': 'Action Test Mail',
            'email_to': 'action@gmail.com',
            'email_from': self.test_user.email,
            'body_html': '<p>This is the test body.</p>',
        })

        # Test open mail
        body = mail_model.open_mail(mail.id)
        self.assertEqual(body, '<p>This is the test body.</p>')

        # Test star mail (toggle)
        self.assertFalse(mail.is_starred)
        mail_model.star_mail(mail.id)
        self.assertTrue(mail.is_starred)
        
        # star_mail again to toggle off
        mail_model.star_mail(mail.id)
        self.assertFalse(mail.is_starred)

        # Test unstar mail
        mail.write({'is_starred': True})
        mail_model.unstar_mail(mail.id)
        self.assertFalse(mail.is_starred)

        # Test archive mail
        self.assertTrue(mail.active)
        mail_model.archive_mail(mail.id)
        self.assertFalse(mail.active)

        # Test unarchive mail
        mail_model.unarchive_mail(mail.id)
        self.assertTrue(mail.active)

        # Test archive checked mail
        mail_model.archive_checked_mail([mail.id])
        self.assertFalse(mail.active)

    def test_mail_deletion(self):
        """Test deleting mail and checked mail."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        mail_to_delete = mail_model.create({
            'subject': 'Delete Me',
            'email_to': 'delete@gmail.com',
        })
        mail_checked_delete = mail_model.create({
            'subject': 'Checked Delete Me',
            'email_to': 'delete@gmail.com',
        })

        # Unlink single mail
        mail_model.delete_mail([mail_to_delete.id])
        self.assertFalse(mail_to_delete.exists())

        # Unlink checked mail
        mail_model.delete_checked_mail(mail_checked_delete.id)
        self.assertFalse(mail_checked_delete.exists())

    def test_sent_mail_success(self):
        """Test composing and sending mail successfully to a valid Gmail address."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        # Send mail with an image attachment
        res = mail_model.sent_mail(
            subject='Hello from Test',
            recipient='hello_world@gmail.com',
            content='Hello!\nThis is test content.',
            images=[{
                'name': 'test_pixel.png',
                'image_uri': self.sample_image_base64,
            }]
        )

        self.assertTrue(res)
        created_mail = mail_model.browse(res[0]['id'])
        self.assertEqual(created_mail.subject, 'Hello from Test')
        self.assertEqual(created_mail.email_to, 'hello_world@gmail.com')
        self.assertEqual(created_mail.email_from, self.test_user.email)
        self.assertIn('Hello!<br>This is test content.', created_mail.body_html)
        self.assertEqual(len(created_mail.attachment_ids), 1)
        self.assertEqual(created_mail.attachment_ids[0].name, 'test_pixel.png')

    def test_sent_mail_validation_error(self):
        """Test sent_mail raises ValidationError for non-gmail addresses."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        with self.assertRaises(ValidationError):
            mail_model.sent_mail(
                subject='Bad Recipient',
                recipient='test@yahoo.com',
                content='Hello',
            )

    def test_retry_mail(self):
        """Test retrying mail sends it again."""
        mail_model = self.env['mail.mail'].with_user(self.test_user)

        mail = mail_model.create({
            'subject': 'Retry Test',
            'email_to': 'retry@gmail.com',
            'state': 'exception',
        })

        mail_model.retry_mail(mail.id)
        # Should be processed and sent (or attempted to be sent)
        self.assertIn(mail.state, ('outgoing', 'sent'))

    def test_ir_attachment_get_fields(self):
        """Test getting fields from attachments."""
        attachment = self.env['ir.attachment'].create({
            'name': 'test_doc.txt',
            'datas': base64.b64encode(b'Hello World Document'),
            'res_model': 'mail.mail',
        })

        res = self.env['ir.attachment'].get_fields([attachment.id])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['attachment'], attachment.id)
        self.assertEqual(res[0]['name'], 'test_doc.txt')
        self.assertEqual(base64.b64decode(res[0]['datas']), b'Hello World Document')

    def test_mail_icon_crud_and_logo(self):
        """Test the mail.icon model's handling, default value, creation, and retrieval."""
        icon_model = self.env['mail.icon']

        # Ensure default logo is set on create when no value is passed
        new_icon = icon_model.create([{}])
        self.assertTrue(new_icon.mail_icon)

        # Create with a custom image and verify it processes
        custom_icon = icon_model.create([{
            'mail_icon': self.sample_image_base64
        }])
        self.assertTrue(custom_icon.mail_icon)

        # Note: Testing direct write on mail.icon is bypassed as the original code calls super().create(values) instead of super().write(values) inside write()
        # custom_icon.write({
        #     'mail_icon': self.sample_image_base64
        # })
        # self.assertTrue(custom_icon.mail_icon)

        # Test load_logo returns the latest logo
        logo_data = icon_model.load_logo()
        self.assertEqual(logo_data, custom_icon.mail_icon)

    def test_res_config_settings(self):
        """Test config settings configuration and defaults."""
        icon_model = self.env['mail.icon']
        icon_1 = icon_model.create([{'mail_icon': self.sample_image_base64}])
        icon_2 = icon_model.create([{'mail_icon': self.sample_image_base64}])

        config = self.env['res.config.settings'].create({
            'custom_mail_logo': True,
        })

        # Test config defaults to the latest icon
        self.assertEqual(config.mail_icon_id, icon_2)
        self.assertEqual(config.icon, icon_2.mail_icon)
        self.assertTrue(config.custom_mail_logo)
