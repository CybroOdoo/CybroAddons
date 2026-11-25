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
from odoo.tools import html2plaintext

from .jira_client import JIRA_ERRORS, JiraClient

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    """Extends mail.message to integrate with Jira comments."""
    _inherit = 'mail.message'

    message_id_jira = fields.Integer(string='Jira Comment ID',
                                     help='ID of the matching comment in Jira.')

    @api.model_create_multi
    def create(self, vals_list):
        """Create messages and, in Automatic mode, post the comments written
        on synced tasks to Jira."""
        messages = super().create(vals_list)
        client = JiraClient.for_automatic_sync(self.env)
        if client:
            for message in messages.filtered(
                    lambda m: m.model == 'project.task' and m.res_id
                    and m.message_type == 'comment' and not m.message_id_jira):
                task = self.env['project.task'].sudo().browse(message.res_id).exists()
                text = html2plaintext(message.body or '').strip()
                if not (task.task_id_jira and text):
                    continue
                try:
                    message.message_id_jira = client.add_comment(task.task_id_jira, text)
                except (*JIRA_ERRORS, KeyError) as error:
                    _logger.error("Failed to post a comment on Jira issue %s: %s",
                                  task.task_id_jira, error)
        return messages
