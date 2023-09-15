# -*- coding: utf-8 -*-
###################################################################################
#    Activity Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import date, datetime
from collections import defaultdict
import pytz

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError


class MailActivity(models.Model):
    """Inherited mail.activity model
    mostly to add dashboard functionalities"""
    _inherit = "mail.activity"

    state = fields.Selection([
        ('overdue', 'Overdue'), ('today', 'Today'), ('planned', 'Planned'),
        ('done', 'Done'), ('cancel', 'Cancelled')], string='State',
        help='Track state of activity.',
        compute='_compute_state', store=True)
    active = fields.Boolean(string='Active',
                            help='Default field to archive',
                            default=True)
    type = fields.Selection(
        [('overdue', 'Overdue'), ('today', 'Today'), ('planned', 'Planned'),
         ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Type', help='Choose the type of activity.')

    activity_tag_ids = fields.Many2many('activity.tag', string='Activity Tags',
                                        help='Select activity tags.')

    def activity_cancel(self):
        """cancel activity"""
        for rec in self:
            if rec.state == 'cancel':
                raise UserError(
                    _("You Cant Cancel this activity %s") % rec.res_name)
            else:
                rec.action_cancel()

    def activity_done(self):
        """done activity"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    _("You Cant Cancel this activity %s") % rec.res_name)
            else:
                rec._action_done()

    def get_activity_count(self):
        """get the activity count details"""
        activity = self.env['mail.activity']
        domain = []
        if self.env.user._is_admin():
            domain = domain
        else:
            domain.append(('user_id', '=', self.env.user.id), )
        all = activity.with_context(active_test=False).search(domain)
        planned = all.filtered(lambda x: x.state == 'planned')
        overdue = all.filtered(lambda x: x.state == 'overdue')
        today = all.filtered(lambda x: x.state == 'today')
        done = all.filtered(lambda x: x.state == 'done')
        cancel = all.filtered(lambda x: x.state == 'cancel')
        res = {
            'len_all': len(all),
            'len_overdue': len(overdue),
            'len_planned': len(planned),
            'len_today': len(today),
            'len_done': len(done),
            'len_cancel': len(cancel)
        }
        return res

    def get_activity(self, id):
        activity = self.env['mail.activity'].browse(id)
        return {
            'model': activity.res_model,
            'res_id': activity.res_id
        }

    def _action_done(self, feedback=False, attachment_ids=None):
        """action done function: rewrite the function"""
        messages = self.env['mail.message']
        next_activities_values = []

        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])

        for activity in self:
            if activity.chaining_type == 'trigger':
                vals = activity.with_context(
                    activity_previous_deadline=activity.date_deadline)._prepare_next_activity_values()
                next_activities_values.append(vals)

            # post message on activity, before deleting it
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={
                    'activity': activity,
                    'feedback': feedback,
                    'display_assignee': activity.user_id != self.env.user
                },
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id(
                    'mail.mt_activities'),
                mail_activity_type_id=activity.activity_type_id.id,
                attachment_ids=[Command.link(attachment_id) for attachment_id in
                                attachment_ids] if attachment_ids else [],
            )

            activity_message = record.message_ids[0]
            message_attachments = self.env['ir.attachment'].browse(
                activity_attachments[activity.id])
            if message_attachments:
                message_attachments.write({
                    'res_id': activity_message.id,
                    'res_model': activity_message._name,
                })
                activity_message.attachment_ids = message_attachments
            messages |= activity_message

        next_activities = self.env['mail.activity'].create(
            next_activities_values)
        for rec in self:
            rec.state = 'done'
            rec.active = False
        return messages, next_activities

    @api.model
    def _compute_state_from_date(self, date_deadline, tz=False):
        """Compute the state"""
        date_deadline = fields.Date.from_string(date_deadline)
        today_default = date.today()
        today = today_default
        if tz:
            today_utc = pytz.utc.localize(datetime.utcnow())
            today_tz = today_utc.astimezone(pytz.timezone(tz))
            today = date(year=today_tz.year, month=today_tz.month,
                         day=today_tz.day)
        diff = (date_deadline - today)
        for rec in self:
            if rec.state == 'done':
                return 'done'
            elif rec.type == 'cancel':
                return 'cancel'
            else:
                if diff.days == 0:
                    return 'today'
                elif diff.days < 0:
                    return 'overdue'
                else:
                    return 'planned'

    def action_cancel(self):
        """cancel activities"""
        for rec in self:
            rec.state = 'cancel'

    @api.depends('state')
    def _onchange_state(self):
        """change state and type"""
        for rec in self:
            rec.type = rec.state
