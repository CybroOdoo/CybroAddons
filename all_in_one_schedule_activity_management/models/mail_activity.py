# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from collections import defaultdict
from datetime import date

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class MailActivity(models.Model):
    """This class is used to inherit the mail.activity model"""

    _inherit = "mail.activity"

    state = fields.Selection(
        [
            ("overdue", "Overdue"),
            ("today", "Today"),
            ("planned", "Planned"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        "State",
        compute="_compute_state",
        store=True,
        help="state for the activity",
    )
    active = fields.Boolean("Active", default=True,
                            help="The record make Active")
    activity_type = fields.Many2many(
        "activity.tag", string="Activity Type",
        help="Activity type"
    )

    def action_mail_on_due_date(self):
        """This function is used to send mails on due date"""
        activity_email = self.env["mail.activity"].search([])
        notification_on_date = (
            self.env["ir.config_parameter"].sudo().get_param("notify_on_due_date")
        )
        notification_on_expiry = (
            self.env["ir.config_parameter"].sudo().get_param("notify_on_expiry")
        )
        for rec in activity_email:
            if notification_on_expiry:
                if rec.date_deadline < date.today():
                    self.env["mail.mail"].sudo().create(
                        {
                            "email_from": self.env.company.email,
                            "author_id": self.env.user.partner_id.id,
                            "body_html": "Hello <br> You missed the %s activity for the document %s </br>"
                            % (rec.activity_type_id.name, rec.res_name),
                            "subject": "%s Activity missed" % rec.activity_type_id.name,
                            "email_to": rec.user_id.email,
                        }
                    ).send(auto_commit=False)
            if notification_on_date:
                if rec.date_deadline == date.today():
                    self.env["mail.mail"].sudo().create(
                        {
                            "email_from": self.env.company.email,
                            "author_id": self.env.user.partner_id.id,
                            "body_html": "Hello <br> Today is your %s activity for the document %s </br>"
                            % (rec.activity_type_id.name, rec.res_name),
                            "subject": "Today %s Activity" % rec.activity_type_id.name,
                            "email_to": rec.user_id.email,
                        }
                    ).send(auto_commit=False)

    @api.onchange("res_model", "res_name")
    def _compute_res_id(self):
        """Compute the res id for the document"""
        for rec in self:
            if not rec.res_id:
                if rec.res_model and rec.res_name:
                    res_model_name = self.env["ir.model"].search(
                        [("model", "=", rec.res_model)]
                    )
                    res_model_id = self.env[res_model_name.model].search(
                        [("name", "=", rec.res_name)]
                    )
                    for res in res_model_id:
                        rec.res_id = res.id
                else:
                    return
            else:
                return

    def activity_cancel(self):
        """cancel activity"""
        for rec in self:
            if rec.state == "cancel":
                raise UserError(_("You Cant Cancelled this activity %s") % rec.res_name)
            else:
                rec.action_cancel()

    def activity_done(self):
        """done activity"""
        for rec in self:
            if rec.state == "done":
                raise UserError(_("You Cant Cancelled this activity %s") % rec.res_name)
            else:
                rec._action_done()

    def get_activity_count(self):
        """get the activity count details"""
        activity = self.env["mail.activity"]
        all = activity.search([])
        planned = activity.search([("state", "=", "planned")])
        overdue = activity.search([("state", "=", "overdue")])
        today = activity.search([("state", "=", "today")])
        done = activity.search([("state", "=", "done"), ("active", "=", False)])
        cancel = activity.search([("state", "=", "cancel")])
        return {
            "len_all": len(all),
            "len_overdue": len(overdue),
            "len_planned": len(planned),
            "len_today": len(today),
            "len_done": len(done),
            "len_cancel": len(cancel),
        }

    def get_activity(self, id):
        """Function for to get the activity"""
        activity = self.env["mail.activity"].search([("id", "=", id)])
        return {"model": activity.res_model, "res_id": activity.res_id}

    def _action_done(self, feedback=False, attachment_ids=None):
        """action done function: rewrite the function"""
        messages = self.env["mail.message"]
        next_activities_values = []

        attachments = self.env["ir.attachment"].search_read(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ],
            ["id", "res_id"],
        )

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment["res_id"]
            activity_attachments[activity_id].append(attachment["id"])

        for activity in self:
            if activity.chaining_type == "trigger":
                vals = activity.with_context(
                    activity_previous_deadline=activity.date_deadline
                )._prepare_next_activity_values()
                next_activities_values.append(vals)

            # post message on activity, before deleting it
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                "mail.message_activity_done",
                values={
                    "activity": activity,
                    "feedback": feedback,
                    "display_assignee": activity.user_id != self.env.user,
                },
                subtype_id=self.env["ir.model.data"]._xmlid_to_res_id(
                    "mail.mt_activities"
                ),
                mail_activity_type_id=activity.activity_type_id.id,
                attachment_ids=[
                    Command.link(attachment_id) for attachment_id in attachment_ids
                ]
                if attachment_ids
                else [],
            )

            activity_message = record.message_ids[0]
            message_attachments = self.env["ir.attachment"].browse(
                activity_attachments[activity.id]
            )
            if message_attachments:
                message_attachments.write(
                    {
                        "res_id": activity_message.id,
                        "res_model": activity_message._name,
                    }
                )
                activity_message.attachment_ids = message_attachments
            messages |= activity_message

        next_activities = self.env["mail.activity"].create(next_activities_values)
        for rec in self:
            rec.state = "done"
            rec.active = False

        return messages, next_activities

    def action_cancel(self):
        """cancel activities"""
        for rec in self:
            rec.state = "cancel"

    @api.depends("state")
    def _onchange_state(self):
        """change state and type"""
        for rec in self:
            rec.type = rec.state
