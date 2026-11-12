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
import json
import logging

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import Stream
from odoo.tools.image import image_process

_logger = logging.getLogger(__name__)

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_URL = (
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    "&fields=id,name,mimeType,webViewLink,size,modifiedTime,thumbnailLink")
THUMBNAIL_SIZE = (256, 256)


class IrAttachment(models.Model):
    """Inherit ir.attachment to add automatic Google Drive sync
    capabilities."""
    _inherit = 'ir.attachment'

    google_file_id = fields.Char(string='Google File ID', readonly=True)
    google_file_url = fields.Char(string='Google File URL', readonly=True)
    is_google_synced = fields.Boolean(string='Synced to Google')
    google_last_sync = fields.Datetime(string='Google Last sync')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically sync new attachments to Google
        Drive.

        :param list vals_list: Values for creating ir.attachment records.
        :return: Created ir.attachment records.
        :rtype: ir.attachment
        """
        attachments = super().create(vals_list)
        if self.env.context.get("no_google_upload"):
            return attachments
        if not self.env["google.drive.account"]._get_connected_account():
            return attachments
        for attachment in attachments._filter_google_syncable():
            attachment._auto_sync_to_google_drive()
        return attachments

    def write(self, vals):
        """Override write to sync updated attachment binary data to Google
        Drive.

        :param dict vals: Values to update on ir.attachment.
        :return: Boolean indicating success.
        :rtype: bool
        """
        res = super().write(vals)
        if self.env.context.get('no_google_upload') or "datas" not in vals:
            return res
        if not self.env["google.drive.account"]._get_connected_account():
            return res
        for rec in self._filter_google_syncable().filtered(
                lambda a: a.datas and not a.google_file_id):
            rec._auto_sync_to_google_drive()
        return res

    def _filter_google_syncable(self):
        """Return only user documents that are safe to offload to Google Drive.

        Asset bundles and other URL-served files (``url`` set) and binary
        field storage (``res_field`` set, e.g. avatars, menu icons) must keep
        their local content, otherwise Odoo serves them empty.
        """
        return self.filtered(
            lambda a: a.type == 'binary' and not a.url and not a.res_field
        )

    def _get_google_account(self):
        """Return the connected Google Drive account.

        :raises UserError: If no Google Drive account is connected.
        """
        account = self.env["google.drive.account"]._get_connected_account()
        if not account:
            raise UserError(_("No Google Drive account is connected."))
        return account

    def _auto_sync_to_google_drive(self):
        """Upload the attachment without blocking its creation on failure.

        Errors from Google are logged and the attachment is kept locally and
        flagged as failed in the Google Drive dashboard.
        """
        self.ensure_one()
        try:
            self._sync_to_google_drive()
        except (UserError, requests.RequestException) as error:
            _logger.warning(
                "Could not upload attachment %s to Google Drive: %s",
                self.id, error)
            self._set_google_attachment({"state": "failed"})

    def _sync_to_google_drive(self):
        """Upload attachment and synchronize metadata."""
        self.ensure_one()
        if self.google_file_id:
            return
        google_file = self._upload_to_google_drive()
        if not google_file:
            return
        self._mark_as_google_storage(google_file)
        self._create_google_attachment(google_file)
        if not self._get_google_account().keep_local_copy:
            self._remove_local_binary()

    def _set_google_attachment(self, vals):
        """Create or update the google.drive.attachment record of the file.

        :param dict vals: Values to write on the tracking record.
        """
        self.ensure_one()
        google_attachment = self.env["google.drive.attachment"].sudo(
            ).with_context(no_google_upload=True)
        record = google_attachment.search(
            [("attachment_id", "=", self.id)], limit=1)
        if record:
            record.write(vals)
        else:
            google_attachment.create(dict(vals, attachment_id=self.id))

    def _fetch_google_thumbnail(self, google_file):
        """Fetch a thumbnail of the uploaded file from Google Drive.

        :param dict google_file: JSON response dict returned by Google Drive.
        Images are downscaled locally so the full file content is never
        stored as thumbnail.

        :return: Base64 encoded thumbnail or False.
        """
        file_id = google_file.get("id")
        if not file_id:
            return False
        try:
            headers = self._get_google_account()._get_headers()
            if google_file.get("mimeType", "").startswith("image/"):
                response = requests.get(
                    f"{DRIVE_FILES_URL}/{file_id}?alt=media",
                    headers=headers, timeout=30)
                if response.status_code == 200:
                    return self._make_google_thumbnail(response.content)
                return False
            response = requests.get(
                f"{DRIVE_FILES_URL}/{file_id}",
                params={"fields": "thumbnailLink"},
                headers=headers, timeout=15)
            if response.status_code != 200:
                return False
            link = response.json().get("thumbnailLink")
            if not link:
                return False
            # Replace the size suffix for a higher quality thumbnail
            link = link.rsplit("=s", 1)[0] + "=s400"
            response = requests.get(
                link, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code == 200 and response.content:
                return self._make_google_thumbnail(response.content)
        except (UserError, requests.RequestException) as error:
            _logger.warning(
                "Could not fetch thumbnail for file %s: %s", file_id, error)
        return False

    def _make_google_thumbnail(self, content):
        """Return a downscaled, base64 encoded thumbnail of an image.

        :param bytes content: Raw image content.
        :raises UserError: If the content is not a valid image.
        """
        return base64.b64encode(
            image_process(content, size=THUMBNAIL_SIZE)).decode()

    def _create_google_attachment(self, google_file):
        """Create or update a synced google.drive.attachment record.

        :param dict google_file: JSON response dict returned by Google Drive.
        """
        self._set_google_attachment({
            "google_file_id": google_file["id"],
            "google_file_url": google_file.get("webViewLink"),
            "state": "synced",
            "thumbnail_url": google_file.get("thumbnailLink", ""),
            "thumbnail_data": self._fetch_google_thumbnail(google_file),
        })

    def _upload_to_google_drive(self):
        """Upload the local binary file to Google Drive.

        The file is placed in the folder configured on the account, or in
        the root of My Drive if none is set.

        :return: JSON response dict returned by Google Drive or False.
        :raises UserError: If Google Drive rejects the upload.
        """
        self.ensure_one()
        if not self.datas:
            return False
        account = self._get_google_account()
        metadata = {"name": self.name}
        if account.drive_folder_id:
            metadata["parents"] = [account.drive_folder_id]
        files = {
            "metadata": (None, json.dumps(metadata), "application/json"),
            "file": (
                self.name,
                base64.b64decode(self.datas),
                self.mimetype or "application/octet-stream",
            ),
        }
        response = requests.post(
            DRIVE_UPLOAD_URL,
            headers=account._get_headers(),
            files=files,
            timeout=60,
        )
        if response.status_code != 200:
            raise UserError(_(
                "Google Drive Upload Error: %s", response.text))
        return response.json()

    def action_download_from_google(self):
        """Download the file from Google Drive and store it back in Odoo."""
        self.ensure_one()
        if not self.google_file_id:
            return
        account = self.env["google.drive.account"]._get_connected_account()
        if not account:
            return
        binary = account.download_file(self.google_file_id)
        self.with_context(no_google_upload=True).write({
            "datas": base64.b64encode(binary),
        })

    def _mark_as_google_storage(self, google_file):
        """Update attachment metadata to mark as synced with Google Drive.

        :param dict google_file: Upload metadata returned by Google Drive.
        """
        self.ensure_one()
        self.with_context(no_google_upload=True).write({
            "google_file_id": google_file["id"],
            "google_file_url": google_file.get("webViewLink"),
            "is_google_synced": True,
            "google_last_sync": fields.Datetime.now(),
            "file_size": int(google_file.get("size", self.file_size or 0)),
        })

    def _remove_local_binary(self):
        """Remove local binary content from the database when
        keep_local_copy is False."""
        self.ensure_one()
        self.with_context(no_google_upload=True).write({
            "datas": False,
        })

    def action_upload_to_google(self):
        """Upload attachment to Google Drive."""
        for attachment in self:
            attachment._sync_to_google_drive()

    def action_open_google_drive(self):
        """Return URL action to open the file in Google Drive in a new browser
        tab.

        :return: ir.actions.act_url redirecting to Google Drive web view URL.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.google_file_url,
            "target": "new",
        }

    def _to_http_stream(self):
        """Override _to_http_stream to stream files directly from Google Drive
        on demand.

        :return: HTTP Stream object or super result.
        :rtype: odoo.http.Stream
        """
        self.ensure_one()
        if self.google_file_id and not self.store_fname and not self.db_datas:
            account = self.env[
                "google.drive.account"]._get_connected_account()
            if account:
                try:
                    binary = account.download_file(self.google_file_id)
                except (UserError, requests.RequestException) as error:
                    _logger.warning(
                        "Could not stream attachment %s from Google Drive: %s",
                        self.id, error)
                    binary = False
                if binary:
                    stream = Stream(
                        mimetype=self.mimetype,
                        download_name=self.name,
                        etag=self.checksum,
                        public=self.public,
                    )
                    stream.type = 'data'
                    stream.data = binary
                    stream.last_modified = self.write_date
                    stream.size = len(binary)
                    return stream
        return super()._to_http_stream()
