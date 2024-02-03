# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
from collections import defaultdict
from odoo import fields, models


class MailActivity(models.Model):
    """Inherited mail.activity model mostly to add dashboard functionalities"""
    _inherit = "mail.activity"

    activity_tag_ids = fields.Many2many('activity.tag',
                                        string='Activity Tags',
                                        help='Select activity tags.')
    state = fields.Selection([
        ('planned', 'Planned'),
        ('today', 'Today'),
        ('done', 'Done'),
        ('overdue', 'Overdue')], string='State', help='State of the activity',
        compute='_compute_state', store=True)

    def _action_done(self, feedback=False, attachment_ids=None):
        """Override _action_done to remove the unlink code"""
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []
        # Search for all attachments linked to the activities we are about to
        # unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])
        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])
        for model, activity_data in self._classify_by_model().items():
            records = self.env[model].browse(activity_data['record_ids'])
            for record, activity in zip(records, activity_data['activities']):
                # extract value to generate next activities
                if activity.chaining_type == 'trigger':
                    vals = (activity.with_context(
                        activity_previous_deadline=activity.date_deadline).
                            _prepare_next_activity_values())
                    next_activities_values.append(vals)
                # post message on activity, before deleting it
                activity_message = record.message_post_with_source(
                    'mail.message_activity_done',
                    attachment_ids=attachment_ids,
                    render_values={
                        'activity': activity,
                        'feedback': feedback,
                        'display_assignee': activity.user_id != self.env.user
                    },
                    mail_activity_type_id=activity.activity_type_id.id,
                    subtype_xmlid='mail.mt_activities',
                )
                if activity.activity_type_id.keep_done:
                    attachment_ids = ((attachment_ids or [])
                                      + activity_attachments.get(activity.id,
                                                                 []))
                    if attachment_ids:
                        activity.attachment_ids = attachment_ids
                # Moving the attachments in the message
                # TODO: Fix void res_id on attachment when you create an
                #  activity with an image
                # directly, see route /web_editor/attachment/add
                if activity_attachments[activity.id]:
                    message_attachments = self.env['ir.attachment'].browse(
                        activity_attachments[activity.id])
                    if message_attachments:
                        message_attachments.write({
                            'res_id': activity_message.id,
                            'res_model': activity_message._name,
                        })
                        activity_message.attachment_ids = message_attachments
                messages += activity_message
        next_activities = self.env['mail.activity']
        if next_activities_values:
            next_activities = self.env['mail.activity'].create(
                next_activities_values)
        for rec in self:
            if rec.state != 'done':
                rec.state = 'done'
                rec.active = False
        return messages, next_activities

    def get_activity(self, activity_id):
        """Method for returning model and id of activity"""
        activity = self.env['mail.activity'].browse(activity_id)
        return {
            'model': activity.res_model,
            'res_id': activity.res_id
        }
