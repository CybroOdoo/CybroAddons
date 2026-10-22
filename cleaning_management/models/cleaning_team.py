# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
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

    _name_unique = models.Constraint(
        'UNIQUE(name)', 'The team already exists')

    def _default_emp_detail_ids(self):
        """Returns default values for emp_detail_ids records"""
        return self.env['employee.details'].search([]).ids

    name = fields.Char(string='Team Name', required=True,
                       help="Choose Team Name")
    emp_detail_ids = fields.Many2many('employee.details',
                                      help="Stores records to define domain "
                                           "for field.",
                                      relation="emp_detail_ids_rel",
                                      default=lambda self: self._default_emp_detail_ids())
    team_leader_id = fields.Many2one('employee.details',
                                     string='Leader', required=True,
                                     help="Choose Leader For Team",
                                     domain="[('id', 'in', "
                                            "emp_detail_ids)]")
    members_ids = fields.Many2many('employee.details',
                                   help="Choose Members For Team",
                                   required=True,
                                   domain="[('id', 'in', "
                                          "emp_detail_ids)]")
    duty_type = fields.Selection([('morning', 'Morning'),
                                  ('night', 'Night'),
                                  ('evening', 'Evening')], required=True,
                                 help="Select Duty Type Of The Team")
    cleaning_date = fields.Date(help="Choose Cleaning Date For Team")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     help="Choose Cleaning Time For Team")
    cleaning_duty_id = fields.Many2one("cleaning.team.duty",
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
        details = self.env['employee.details']
        if self.team_leader_id:
            self.members_ids = self.team_leader_id
        if self.duty_type in ["morning", "evening", "night"]:
            same_shift = self.env['cleaning.team'].search([
                ('duty_type', '=', self.duty_type)])
            taken = same_shift.team_leader_id | same_shift.members_ids
            self.emp_detail_ids = details.search([
                ('time_shift_id', '=', f"{self.duty_type.capitalize()} Shift"),
                ('id', 'not in', (taken | self.team_leader_id).ids)])
        else:
            self.emp_detail_ids = details.search([])