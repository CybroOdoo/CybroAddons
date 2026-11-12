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
from odoo import fields, models


class GoogleDriveAttachment(models.Model):
    """Model tracking Google Drive attachment sync status, URLs, and
    thumbnails."""
    _name = 'google.drive.attachment'
    _description = 'Google Drive Attachment'
    _rec_name = 'attachment_id'

    attachment_id = fields.Many2one('ir.attachment', 'Attachment')
    google_file_id = fields.Char(string='Google File ID',
                                 groups='base.group_system')
    google_file_url = fields.Char(string='Google File URL',
                                  groups='base.group_system')
    state = fields.Selection(string='State', selection=[
        ("pending", "Pending"),
        ("synced", "Synced"),
        ("failed", "Failed"),
    ], default="pending")
    thumbnail_url = fields.Char(string='Thumbnail URL',
                                groups='base.group_system')
    thumbnail_data = fields.Binary(string='Thumbnail', attachment=True)

    def action_preview(self):
        """Open the file through Odoo so the user's access rights on the
        attachment are enforced, instead of exposing the Drive link.

        :return: ir.actions.act_url opening the attachment content.
        :rtype: dict
        """
        self.ensure_one()
        self.attachment_id.check_access('read')
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s" % self.attachment_id.id,
            "target": "new",
        }

    def action_download_from_google(self):
        """Download the file from Google Drive into the related attachment."""
        self.ensure_one()
        if self.attachment_id:
            self.attachment_id.action_download_from_google()
