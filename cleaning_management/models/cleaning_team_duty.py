# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models
from pytz import timezone


class CleaningTeamDuty(models.Model):
    """Creating new model  to retrieve comprehensive details regarding
     the duties assigned to each team."""
    _name = "cleaning.team.duty"
    _description = "Cleaning Team Duty"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'team_id'

    team_leader_id = fields.Many2one('hr.employee',
                                     readonly=True,
                                     string="Team Leader",
                                     help="Choose Leader of Corresponding Team")
    team_id = fields.Many2one('cleaning.team', string='Team Name',
                              readonly=True, help="Choose Cleaning team")
    inspection_id = fields.Many2one('cleaning.inspection',
                                    string="Cleaning Inspection",
                                    help="Choose Cleaning Inspection")
    cleaning_id = fields.Many2one('cleaning.booking',
                                  string="Cleaning Booking",
                                  help="Choose Cleaning Booking")
    members_ids = fields.Many2many('hr.employee', string='Members',
                                   readonly=True,
                                   help="Choose Members Of Corresponding Team")
    location_state_id = fields.Many2one('res.country.state',
                                        string="State", readonly=True,
                                        help="Location for Team To Work")
    place = fields.Char(string="Place", readonly=True,
                        help="Enter Place For The Work")
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  readonly=True, help="Choose Customer Name")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     string='Cleaning Time',
                                     readonly=True,
                                     help="Cleaning Time, Booked By Customer")
    cleaning_date = fields.Date(string='Cleaning Date',
                                readonly=True,
                                help="Cleaning Date That Booked By Customer")
    inspection_boolean = fields.Boolean(string="Is Inspection", default=True,
                                        readonly=True,
                                        help="Got 'INSPECTION' button in"
                                             " form view")
    start_time = fields.Char(string="Start Time",
                             help="Real time to complete all cleaning process")
    start_cleaning = fields.Boolean(string="Is Started")
    end_time = fields.Char(string="End Time",
                           help="Real time to complete all cleaning process")
    end_cleaning = fields.Boolean(string="Is Ended",
                                  help="Real time to end all cleaning process")
    state = fields.Selection([('draft', 'Draft'),
                              ('dirty', 'Dirty'),
                              ('cleaned', 'Cleaned'),
                              ('cancelled', 'Cancelled')],
                             default='draft', string='Status',
                             help="Stages For Cleaning Team Duty",
                             tracking=True)
    inspection_count = fields.Integer(compute="_compute_inspection_count",
                                      string='Inspection Count')

    def action_start(self):
        """Function for start cleaning processes"""
        user_tz = self.env.user.tz or 'UTC'
        start_time_utc = fields.Datetime.now()
        start_time_user_tz = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, start_time_utc).astimezone(
                timezone(user_tz)))

        self.write({
            'start_time': start_time_user_tz,
            'start_cleaning': True
        })

    def action_finish(self):
        """Function for finish cleaning processes"""
        if self.start_cleaning:
            user_tz = self.env.user.tz or 'UTC'
            end_time_utc = fields.Datetime.now()
            end_time_user_tz = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self,
                                                  end_time_utc).astimezone(
                    timezone(user_tz)))
            self.write({
                'end_time': end_time_user_tz,
                'inspection_boolean': False,
                'end_cleaning': True
            })
            start_time_utc = fields.Datetime.from_string(self.start_time)
            end_time_utc = fields.Datetime.from_string(end_time_user_tz)
            total_hours = (end_time_utc - start_time_utc).total_seconds() / 3600
            self.cleaning_id.total_hour_of_working = total_hours

    def action_inspection(self):
        """Clicking the "Inspection" button will direct the user
        to the inspection page."""
        self.inspection_boolean = True
        return {
            'name': 'cleaning_team_id',
            'res_model': 'cleaning.inspection',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {'default_cleaning_team_id': self.team_id.id,
                        'default_inspector_name_id': self.env.user.id,
                        'default_cleaning_id': self.cleaning_id.id,
                        'default_date_from': self.start_time,
                        'default_date_to': self.end_time,
                        'default_cleaning_team_duty_id': self.id
                        }
        }

    def action_view_inspection(self):
        """Function for Open Inspection Smart Button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inspection',
            'view_mode': 'tree,form',
            'res_model': 'cleaning.inspection',
            'domain': [('cleaning_team_duty_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_inspection_count(self):
        """Function for getting total count of inspections"""
        for record in self:
            record.inspection_count = self.env['cleaning.inspection'].search_count(
                [('cleaning_team_duty_id', '=', self.id)])
