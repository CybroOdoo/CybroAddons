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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import api, fields, models

from .jira_client import JIRA_ERRORS, JiraClient

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    """Extends ir.attachment to integrate with Jira."""
    _inherit = 'ir.attachment'

    attachment_id_jira = fields.Integer(string='Jira Attachment ID',
                                        help='ID of the matching attachment in Jira.')

    @api.model_create_multi
    def create(self, vals_list):
        """Create attachments and, in Automatic mode, upload the ones added
        to synced tasks to Jira."""
        attachments = super().create(vals_list)
        client = JiraClient.for_automatic_sync(self.env)
        if client:
            for attachment in attachments.filtered(
                    lambda a: a.res_model == 'project.task' and a.res_id
                    and not a.attachment_id_jira):
                task = self.env['project.task'].sudo().browse(attachment.res_id).exists()
                if not task.task_id_jira:
                    continue
                try:
                    attachment._jira_upload(client, task.task_id_jira)
                except (*JIRA_ERRORS, KeyError, IndexError) as error:
                    _logger.error("Failed to upload attachment %s to Jira: %s",
                                  attachment.name, error)
        return attachments

    def _jira_upload(self, client, issue_key):
        """Upload this file to a Jira issue and store the Jira attachment id."""
        self.ensure_one()
        if self.type == 'binary' and self.raw:
            self.attachment_id_jira = client.upload_attachment(
                issue_key, self.name, self.raw, self.mimetype)

    def unlink(self):
        """Delete attachments and, in Automatic mode, their Jira copies."""
        client = JiraClient.for_automatic_sync(self.env)
        jira_ids = [attachment.attachment_id_jira for attachment in self
                    if attachment.attachment_id_jira] if client else []
        result = super().unlink()
        for jira_id in jira_ids:
            try:
                client.delete(f'/rest/api/3/attachment/{jira_id}')
            except JIRA_ERRORS as error:
                _logger.error("Failed to delete Jira attachment %s: %s", jira_id, error)
        return result
