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
#############################################################################
from odoo import fields, models


class MailActivitySchedule(models.TransientModel):
    """
    Inheriting mail_activity_schedule model to add a feature of activity
    schedules for multiple users.
    """
    _inherit = 'mail.activity.schedule'

    assign_multiple_user_ids = fields.Many2many(
        'res.users',
        string='Assign Multiple Users',
        domain="[('id', '!=', activity_user_id), ('share', '=', False)]",
        help='Select the other users that you want to schedule the activity'
    )

    def _action_schedule_activities(self):
        """
        Override this method to customize the scheduling of activities for
        multiple users.
        """
        user_ids_to_schedule = []
        if self.activity_user_id:
            user_ids_to_schedule.append(self.activity_user_id.id)
        for user in self.assign_multiple_user_ids:
            if user.id not in user_ids_to_schedule:
                user_ids_to_schedule.append(user.id)

        role_id = (
            self.activity_role_id.id
            if hasattr(self, 'activity_role_id') and self.activity_role_id
            else False
        )
        activity_user_id_fname = (
            self.activity_user_id_fname
            if hasattr(self, 'activity_user_id_fname')
            else False
        )

        created_records = self.env['mail.activity']
        for user_id in user_ids_to_schedule:
            if not self.res_model:
                record = self._action_schedule_activities_personal_for_user(
                    user_id
                )
            else:
                record = self._get_applied_on_records().activity_schedule(
                    activity_type_id=self.activity_type_id.id,
                    automated=False,
                    summary=self.summary,
                    note=self.note,
                    user_id=user_id,
                    role_id=role_id,
                    date_deadline=self.date_deadline,
                    activity_user_id_fname=activity_user_id_fname,
                )
            if record:
                created_records |= record

        scheduled_user_ids = created_records.mapped('user_id.id')
        if (
            self.activity_user_id
            and self.activity_user_id.id in scheduled_user_ids
        ):
            return created_records.filtered(
                lambda r: r.user_id == self.activity_user_id
            )
        return created_records

    def _action_schedule_activities_personal_for_user(self, user_id):
        role_id = (
            self.activity_role_id.id
            if hasattr(self, 'activity_role_id') and self.activity_role_id
            else False
        )
        return self.env['mail.activity'].create({
            'activity_type_id': self.activity_type_id.id,
            'automated': False,
            'date_deadline': self.date_deadline,
            'note': self.note,
            'res_id': False,
            'res_model_id': False,
            'summary': self.summary,
            'user_id': user_id,
            'role_id': role_id,
        })


