# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class MailActivitySchedule(models.TransientModel):
    """
    Inheriting mail_activity_schedule model to add a feature of activity
    schedules for multiple users.
    """
    _inherit = 'mail.activity.schedule'

    assign_multiple_user_ids = fields.Many2many('res.users',
                                                domain="[('id', '!=',"
                                                       " activity_user_id)]",
                                                help='Select the other users '
                                                     'that you want to '
                                                     'schedule the activity')

    def _action_schedule_activities(self):
        """
        Override this method to customize the scheduling of activities for
        multiple users.
        """
        user_ids_to_schedule = [user.id for user in
                                self.assign_multiple_user_ids] + [
                                   self.activity_user_id.id]

        created_records = {}
        for user_id in user_ids_to_schedule:
            record = self._get_applied_on_records().activity_schedule(
                activity_type_id=self.activity_type_id.id,
                summary=self.summary,
                note=self.note,
                user_id=user_id,
                date_deadline=self.date_deadline
            )
            created_records[user_id] = record
        return created_records.get(self.activity_user_id.id)
