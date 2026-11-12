# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
###############################################################################
import base64
import io
import json
from unittest.mock import patch
import requests
from PIL import Image
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from .common import GOOGLE_FILE, create_account, mock_response

REQUESTS_PATH = ('odoo.addons.google_drive_odoo_connector.models.'
                 'ir_attachment.requests')
DOWNLOAD_PATH = ('odoo.addons.google_drive_odoo_connector.models.'
                 'google_drive_account.GoogleDriveAccount.download_file')
BASE_STREAM_PATH = ('odoo.addons.base.models.ir_attachment.IrAttachment.'
                    '_to_http_stream')
FILE_CONTENT = b'hello world'


@tagged('post_install', '-at_install')
class TestIrAttachment(TransactionCase):
    """Test cases for the ir.attachment extension defined in
    google_drive_odoo_connector/models/ir_attachment.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Make sure no pre-existing account from the database interferes
        cls.env['google.drive.account'].search([]).write({'state': 'draft'})
        cls.account = create_account(cls.env)
        cls.Attachment = cls.env['ir.attachment']

    def _attachment_vals(self, **vals):
        values = {
            'name': 'test.txt',
            'datas': base64.b64encode(FILE_CONTENT),
            'mimetype': 'text/plain',
        }
        values.update(vals)
        return values

    def _patch_upload(self, status_code=200, json_data=None):
        """Patch the Drive upload and thumbnail requests."""
        post = patch(REQUESTS_PATH + '.post', return_value=mock_response(
            status_code=status_code,
            json_data=GOOGLE_FILE if json_data is None else json_data,
            text='upload error'))
        get = patch(REQUESTS_PATH + '.get',
                    return_value=mock_response(status_code=404))
        return post, get

    def _create_local(self, **vals):
        """Create an attachment that is not uploaded to Google Drive."""
        return self.Attachment.with_context(no_google_upload=True).create(
            self._attachment_vals(**vals)).with_context(no_google_upload=False)

    def _create_synced(self, **vals):
        post, get = self._patch_upload()
        with post as mock_post, get:
            attachment = self.Attachment.create(self._attachment_vals(**vals))
        return attachment, mock_post

    # ------------------------------------------------------------------
    # create / write
    # ------------------------------------------------------------------
    def test_create_without_connected_account(self):
        """No upload happens when no account is connected."""
        self.account.state = 'draft'
        with patch(REQUESTS_PATH + '.post') as post:
            attachment = self.Attachment.create(self._attachment_vals())
        post.assert_not_called()
        self.assertFalse(attachment.google_file_id)
        self.assertEqual(base64.b64decode(attachment.datas), FILE_CONTENT)

    def test_create_with_no_google_upload_context(self):
        """The no_google_upload context disables the automatic upload."""
        with patch(REQUESTS_PATH + '.post') as post:
            attachment = self.Attachment.with_context(
                no_google_upload=True).create(self._attachment_vals())
        post.assert_not_called()
        self.assertFalse(attachment.google_file_id)

    def test_create_uploads_and_removes_local_copy(self):
        """A new attachment is uploaded and its local binary removed."""
        attachment, post = self._create_synced()
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs['headers'],
                         {'Authorization': 'Bearer access-token'})
        file_part = post.call_args.kwargs['files']['file']
        self.assertEqual(file_part, ('test.txt', FILE_CONTENT, 'text/plain'))
        self.assertEqual(attachment.google_file_id, GOOGLE_FILE['id'])
        self.assertEqual(attachment.google_file_url,
                         GOOGLE_FILE['webViewLink'])
        self.assertTrue(attachment.is_google_synced)
        self.assertTrue(attachment.google_last_sync)
        self.assertFalse(attachment.datas)

    def test_create_keeps_local_copy(self):
        """keep_local_copy keeps the binary in Odoo after the upload."""
        self.account.keep_local_copy = True
        attachment, dummy = self._create_synced()
        self.assertEqual(attachment.google_file_id, GOOGLE_FILE['id'])
        self.assertEqual(base64.b64decode(attachment.datas), FILE_CONTENT)

    def test_create_google_drive_attachment_record(self):
        """A google.drive.attachment tracking record is created."""
        attachment, dummy = self._create_synced()
        record = self.env['google.drive.attachment'].search(
            [('attachment_id', '=', attachment.id)])
        self.assertEqual(len(record), 1)
        self.assertEqual(record.google_file_id, GOOGLE_FILE['id'])
        self.assertEqual(record.google_file_url, GOOGLE_FILE['webViewLink'])
        self.assertEqual(record.state, 'synced')
        self.assertEqual(record.thumbnail_url, GOOGLE_FILE['thumbnailLink'])

    def _create_image(self, content):
        """Create an image attachment whose Drive download returns content."""
        image_file = dict(GOOGLE_FILE, mimeType='image/png')
        post = patch(REQUESTS_PATH + '.post',
                     return_value=mock_response(json_data=image_file))
        get = patch(REQUESTS_PATH + '.get',
                    return_value=mock_response(content=content))
        with post, get as mock_get:
            attachment = self.Attachment.create(self._attachment_vals(
                name='image.png', mimetype='image/png'))
        self.assertIn('?alt=media', mock_get.call_args.args[0])
        return self.env['google.drive.attachment'].search(
            [('attachment_id', '=', attachment.id)])

    def test_create_image_fetches_thumbnail(self):
        """For images, a downscaled copy is stored as thumbnail."""
        buffer = io.BytesIO()
        Image.new('RGB', (1000, 800), 'red').save(buffer, format='PNG')
        record = self._create_image(buffer.getvalue())
        thumbnail = Image.open(io.BytesIO(
            base64.b64decode(record.thumbnail_data)))
        self.assertLessEqual(max(thumbnail.size), 256)

    def test_create_invalid_image_thumbnail(self):
        """Content that is not an image does not block the sync."""
        record = self._create_image(b'not an image')
        self.assertEqual(record.state, 'synced')
        self.assertFalse(record.thumbnail_data)

    def test_create_thumbnail_error_does_not_block_sync(self):
        """A failure while fetching the thumbnail is only logged."""
        post = patch(REQUESTS_PATH + '.post',
                     return_value=mock_response(json_data=GOOGLE_FILE))
        get = patch(REQUESTS_PATH + '.get',
                    side_effect=requests.ConnectionError('network down'))
        with post, get:
            attachment = self.Attachment.create(self._attachment_vals())
        record = self.env['google.drive.attachment'].search(
            [('attachment_id', '=', attachment.id)])
        self.assertEqual(record.state, 'synced')
        self.assertFalse(record.thumbnail_data)

    def test_create_upload_error(self):
        """A Drive API error does not block the attachment creation."""
        post, get = self._patch_upload(status_code=403)
        with post, get:
            attachment = self.Attachment.create(self._attachment_vals())
        self.assertFalse(attachment.google_file_id)
        self.assertEqual(base64.b64decode(attachment.datas), FILE_CONTENT)
        record = self.env['google.drive.attachment'].search(
            [('attachment_id', '=', attachment.id)])
        self.assertEqual(record.state, 'failed')

    def test_action_upload_error(self):
        """A manual upload reports Drive API errors to the user."""
        attachment = self._create_local()
        post, get = self._patch_upload(status_code=403)
        with post, get, self.assertRaises(UserError):
            attachment.action_upload_to_google()

    def test_upload_to_configured_folder(self):
        """Files are uploaded to the Drive folder set on the account."""
        self.account.drive_folder_id = 'folder_123'
        dummy, post = self._create_synced()
        metadata = json.loads(post.call_args.kwargs['files']['metadata'][1])
        self.assertEqual(metadata, {'name': 'test.txt',
                                    'parents': ['folder_123']})

    def test_upload_to_root_without_folder(self):
        """Without a folder, files are uploaded to the Drive root."""
        dummy, post = self._create_synced()
        metadata = json.loads(post.call_args.kwargs['files']['metadata'][1])
        self.assertEqual(metadata, {'name': 'test.txt'})

    def test_create_as_internal_user(self):
        """Users without access to the account can still create files."""
        user = new_test_user(self.env, login='gdrive_internal',
                             groups='base.group_user')
        post, get = self._patch_upload()
        with post as mock_post, get:
            attachment = self.Attachment.with_user(user).create(
                self._attachment_vals())
        mock_post.assert_called_once()
        self.assertEqual(attachment.sudo().google_file_id, GOOGLE_FILE['id'])

    def test_create_skips_non_syncable_attachments(self):
        """URL attachments and binary field storage are never uploaded."""
        with patch(REQUESTS_PATH + '.post') as post:
            url_attachment = self.Attachment.create({
                'name': 'link', 'type': 'url', 'url': 'https://odoo.com'})
            field_attachment = self.Attachment.create(self._attachment_vals(
                res_model='res.partner', res_id=self.env.user.partner_id.id,
                res_field='image_1920'))
        post.assert_not_called()
        self.assertFalse(url_attachment.google_file_id)
        self.assertFalse(field_attachment.google_file_id)

    def test_filter_google_syncable(self):
        """Only binary attachments without url or res_field are syncable."""
        attachments = self.Attachment.with_context(
            no_google_upload=True).create([
                self._attachment_vals(name='doc'),
                self._attachment_vals(name='asset', url='/web/assets/x.js'),
                {'name': 'link', 'type': 'url', 'url': 'https://odoo.com'},
            ])
        self.assertEqual(attachments._filter_google_syncable(),
                         attachments[0])

    def test_write_datas_uploads_attachment(self):
        """Writing datas on a not yet synced attachment uploads it."""
        attachment = self._create_local()
        post, get = self._patch_upload()
        with post as mock_post, get:
            attachment.write({'datas': base64.b64encode(b'new content')})
        mock_post.assert_called_once()
        self.assertEqual(attachment.google_file_id, GOOGLE_FILE['id'])

    def test_write_without_datas_does_not_upload(self):
        """Writing other fields does not trigger an upload."""
        attachment = self._create_local()
        with patch(REQUESTS_PATH + '.post') as post:
            attachment.write({'name': 'renamed.txt'})
        post.assert_not_called()

    def test_write_on_synced_attachment_does_not_reupload(self):
        """An attachment already on Drive is not uploaded again."""
        self.account.keep_local_copy = True
        attachment, dummy = self._create_synced()
        with patch(REQUESTS_PATH + '.post') as post:
            attachment.write({'datas': base64.b64encode(b'new content')})
        post.assert_not_called()

    # ------------------------------------------------------------------
    # Manual actions
    # ------------------------------------------------------------------
    def test_get_google_account_without_account(self):
        """_get_google_account raises when no account is connected."""
        self.account.state = 'draft'
        with self.assertRaises(UserError):
            self.Attachment._get_google_account()

    def test_upload_to_google_drive_without_datas(self):
        """Nothing is uploaded for an attachment without content."""
        attachment = self.Attachment.with_context(
            no_google_upload=True).create({'name': 'empty.txt'})
        with patch(REQUESTS_PATH + '.post') as post:
            self.assertFalse(attachment._upload_to_google_drive())
        post.assert_not_called()

    def test_action_upload_to_google(self):
        """The manual upload action syncs only unsynced attachments."""
        attachments = self.Attachment.with_context(
            no_google_upload=True).create([
                self._attachment_vals(name='a.txt'),
                self._attachment_vals(name='b.txt',
                                      google_file_id='already_synced'),
            ])
        post, get = self._patch_upload()
        with post as mock_post, get:
            attachments.action_upload_to_google()
        mock_post.assert_called_once()
        self.assertEqual(attachments[0].google_file_id, GOOGLE_FILE['id'])
        self.assertTrue(attachments[0].is_google_synced)
        self.assertFalse(attachments[0].datas)
        self.assertEqual(attachments[1].google_file_id, 'already_synced')

    def test_action_download_from_google(self):
        """The download action restores the binary from Drive."""
        attachment, dummy = self._create_synced()
        self.assertFalse(attachment.datas)
        with patch(DOWNLOAD_PATH, return_value=FILE_CONTENT) as download:
            attachment.action_download_from_google()
        download.assert_called_once_with(GOOGLE_FILE['id'])
        self.assertEqual(base64.b64decode(attachment.datas), FILE_CONTENT)

    def test_action_download_from_google_without_file_id(self):
        """Nothing is downloaded for an attachment not on Drive."""
        attachment = self._create_local()
        with patch(DOWNLOAD_PATH) as download:
            attachment.action_download_from_google()
        download.assert_not_called()

    def test_action_open_google_drive(self):
        """The open action points to the Drive web view link."""
        attachment, dummy = self._create_synced()
        action = attachment.action_open_google_drive()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], GOOGLE_FILE['webViewLink'])
        self.assertEqual(action['target'], 'new')

    # ------------------------------------------------------------------
    # _to_http_stream
    # ------------------------------------------------------------------
    def test_to_http_stream_from_google_drive(self):
        """An offloaded attachment is streamed from Google Drive."""
        attachment, dummy = self._create_synced()
        with patch(DOWNLOAD_PATH, return_value=FILE_CONTENT):
            stream = attachment._to_http_stream()
        self.assertEqual(stream.type, 'data')
        self.assertEqual(stream.data, FILE_CONTENT)
        self.assertEqual(stream.size, len(FILE_CONTENT))
        self.assertEqual(stream.download_name, 'test.txt')

    def test_to_http_stream_download_error_falls_back(self):
        """A Drive error falls back to the standard stream."""
        attachment, dummy = self._create_synced()
        with patch(DOWNLOAD_PATH,
                   side_effect=requests.HTTPError('boom')), \
                patch(BASE_STREAM_PATH, return_value='local stream'):
            stream = attachment._to_http_stream()
        self.assertEqual(stream, 'local stream')

    def test_to_http_stream_local_attachment(self):
        """An attachment with local content is not fetched from Drive."""
        attachment = self._create_local()
        with patch(DOWNLOAD_PATH) as download, \
                patch(BASE_STREAM_PATH, return_value='local stream'):
            stream = attachment._to_http_stream()
        download.assert_not_called()
        self.assertEqual(stream, 'local stream')


@tagged('post_install', '-at_install')
class TestGoogleDriveAttachment(TransactionCase):
    """Test cases for google.drive.attachment defined in
    google_drive_odoo_connector/models/google_drive_attachment.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['google.drive.account'].search([]).write({'state': 'draft'})
        cls.account = create_account(cls.env)
        cls.attachment = cls.env['ir.attachment'].with_context(
            no_google_upload=True).create({'name': 'test.txt'})

    def test_default_state(self):
        """New tracking records start in the pending state."""
        record = self.env['google.drive.attachment'].create({
            'attachment_id': self.attachment.id})
        self.assertEqual(record.state, 'pending')
        self.assertEqual(record.display_name, self.attachment.display_name)

    def test_action_download_without_file_id(self):
        """Nothing is downloaded when the record has no Drive file."""
        record = self.env['google.drive.attachment'].create({
            'attachment_id': self.attachment.id})
        with patch(DOWNLOAD_PATH) as download:
            record.action_download_from_google()
        download.assert_not_called()

    def test_action_download_from_google(self):
        """The Kanban Download button restores the attachment binary."""
        attachment = self.env['ir.attachment'].with_context(
            no_google_upload=True).create({
                'name': 'synced.txt',
                'google_file_id': GOOGLE_FILE['id'],
            })
        record = self.env['google.drive.attachment'].create({
            'attachment_id': attachment.id,
            'google_file_id': GOOGLE_FILE['id'],
        })
        with patch(DOWNLOAD_PATH, return_value=b'drive content') as download:
            record.action_download_from_google()
        download.assert_called_once_with(GOOGLE_FILE['id'])
        self.assertEqual(base64.b64decode(attachment.datas), b'drive content')

    def test_record_rule_own_files_only(self):
        """Users only see the Drive files of attachments they created."""
        user_1 = new_test_user(self.env, login='gdrive_user_1',
                               groups='base.group_user')
        user_2 = new_test_user(self.env, login='gdrive_user_2',
                               groups='base.group_user')
        admin = new_test_user(self.env, login='gdrive_admin',
                              groups='base.group_system')
        GoogleAttachment = self.env['google.drive.attachment']
        records = GoogleAttachment
        for user in (user_1, user_2):
            attachment = self.env['ir.attachment'].with_user(
                user).with_context(no_google_upload=True).create(
                    {'name': 'private.txt'})
            records |= GoogleAttachment.create(
                {'attachment_id': attachment.id})
        self.assertEqual(
            GoogleAttachment.with_user(user_1).search(
                [('id', 'in', records.ids)]), records[0])
        self.assertEqual(
            GoogleAttachment.with_user(user_2).search(
                [('id', 'in', records.ids)]), records[1])
        self.assertEqual(
            GoogleAttachment.with_user(admin).search(
                [('id', 'in', records.ids)]), records)
        with self.assertRaises(AccessError):
            records[1].with_user(user_1).read(['thumbnail_data'])

    def test_action_preview_own_file(self):
        """Preview opens the file through Odoo, not the Drive link."""
        user = new_test_user(self.env, login='gdrive_preview_owner',
                             groups='base.group_user')
        attachment = self.env['ir.attachment'].with_user(user).with_context(
            no_google_upload=True).create({'name': 'mine.txt'})
        record = self.env['google.drive.attachment'].create({
            'attachment_id': attachment.id,
            'google_file_url': GOOGLE_FILE['webViewLink'],
        })
        action = record.with_user(user).action_preview()
        self.assertEqual(action['url'], '/web/content/%s' % attachment.id)

    def test_action_preview_other_user_file(self):
        """Users cannot preview the files of other users."""
        owner = new_test_user(self.env, login='gdrive_preview_a',
                              groups='base.group_user')
        other = new_test_user(self.env, login='gdrive_preview_b',
                              groups='base.group_user')
        attachment = self.env['ir.attachment'].with_user(owner).with_context(
            no_google_upload=True).create({'name': 'private.txt'})
        record = self.env['google.drive.attachment'].create({
            'attachment_id': attachment.id})
        with self.assertRaises(AccessError):
            record.with_user(other).action_preview()
        with self.assertRaises(AccessError):
            attachment.with_user(other).check_access('read')

    def test_drive_url_hidden_from_users(self):
        """The raw Drive link is only readable by administrators."""
        user = new_test_user(self.env, login='gdrive_no_url',
                             groups='base.group_user')
        attachment = self.env['ir.attachment'].with_user(user).with_context(
            no_google_upload=True).create({'name': 'mine.txt'})
        record = self.env['google.drive.attachment'].create({
            'attachment_id': attachment.id,
            'google_file_url': GOOGLE_FILE['webViewLink'],
        })
        with self.assertRaises(AccessError):
            record.with_user(user).read(['google_file_url'])

    def test_action_download_without_connected_account(self):
        """Nothing is downloaded when no account is connected."""
        self.account.state = 'draft'
        record = self.env['google.drive.attachment'].create({
            'attachment_id': self.attachment.id,
            'google_file_id': GOOGLE_FILE['id'],
        })
        with patch(DOWNLOAD_PATH) as download:
            record.action_download_from_google()
        download.assert_not_called()
