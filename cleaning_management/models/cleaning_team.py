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
from odoo import api, fields, models


class CleaningTeam(models.Model):
    """Creating a new model for specifying cleaning teams and
    their associated leaders, members and other details."""
    _name = "cleaning.team"
    _description = "Cleaning Team"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_emp_detail_ids(self):
        """Returns default values for emp_detail_ids records"""
        return self.env['employee.details'].search([]).ids

    name = fields.Char(string='Team Name', required=True,
                       help="Choose Team Name")
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The team already exists')]

    emp_detail_ids = fields.Many2many('employee.details',
                                      help="Stores records to define domain "
                                           "for field.",
                                      relation="emp_detail_ids_rel",
                                      default=_default_emp_detail_ids)
    team_leader_id = fields.Many2one('employee.details',
                                     string='Leader', required=True,
                                     help="Choose Leader For Team",
                                     domain="[('id', 'in', "
                                            "emp_detail_ids)]")
    members_ids = fields.Many2many('employee.details',
                                   string='Members',
                                   help="Choose Members For Team",
                                   required=True,
                                   domain="[('id', 'in', "
                                          "emp_detail_ids)]")
    duty_type = fields.Selection([('morning', 'Morning'),
                                  ('night', 'Night'),
                                  ('evening', 'Evening')], string='Duty Type',
                                 required=True,
                                 help="Select Duty Type Of The Team")
    cleaning_date = fields.Date(string='Cleaning Date and Time',
                                help="Choose Cleaning Date For Team")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     string='Cleaning Time',
                                     help="Choose Cleaning Time For Team")
    cleaning_duty_id = fields.Many2one("cleaning.team.duty",
                                       string="Cleaning Duty",
                                       help="Choose Cleaning Duty")
    cleaning_duty_ids = fields.Many2many("cleaning.team.duty",
                                         string="Cleaning Team Duty",
                                         readonly=False,
                                         help="Choose Cleaning Duty")
    inspection_id = fields.Many2one('cleaning.inspection',
                                    string="Cleaning Inspection",
                                    help="Choose Cleaning Inspection")

    @api.onchange('team_leader_id', 'duty_type')
    def _onchange_team_leader_or_duty_type(self):
        """Function for getting Employees with respect to Duty Type"""
        if self.team_leader_id:
            self.write({'members_ids': [(6, 0, [self.team_leader_id.id])]})
        if self.duty_type in ["morning", "evening", "night"]:
            teams_with_same_shift = self.env['cleaning.team'].search([
                ('duty_type', '=', self.duty_type)])
            excluded_leaders = [team.team_leader_id.id for team in
                                teams_with_same_shift]
            excluded_members = [member.id for team in teams_with_same_shift for
                                member in team.members_ids]
            shift = self.env['employee.details'].search([
                ('time_shift_id', '=', f"{self.duty_type.capitalize()} Shift"),
                ('id', 'not in', excluded_leaders)])
            val = [rec.id for rec in shift if
                   rec.id != self.team_leader_id.id and rec.id not in
                   excluded_members]
            self.write({'emp_detail_ids': [(6, 0, self.env[
                    'employee.details'].search([('id', 'in', val)]).ids)]})
        else:
            self.write({'emp_detail_ids': [(6, 0, self.env[
                    'employee.details'].search([]).ids)]})
