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


class CleaningInspection(models.Model):
    """Create a new model for detailing cleaning inspection specifics.
    The system will incorporate two buttons to indicate the
    cleaning status: "Clean" and "Dirty"."""
    _name = "cleaning.inspection"
    _description = "Cleaning Inspection"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'cleaning_team_id'

    inspector_name_id = fields.Many2one('res.users',
                                        string='Inspector Name',
                                        required=True,
                                        help="Choose Inspector Name")
    cleaning_id = fields.Many2one('cleaning.booking',
                                  help="Cleaning Management",
                                  string="Select Cleaning Management")
    inspection_date_and_time = fields.Datetime(
        string='Inspection Date and Time',
        required=True,
        help="Choose Inspection date and time")
    cleaning_team_id = fields.Many2one('cleaning.team',
                                       string='Cleaning Team',
                                       required=True,
                                       help="Choose cleaning team")
    cleaning_team_duty_id = fields.Many2one('cleaning.team.duty',
                                            string='Cleaning Team Duty',
                                            required=True,
                                            help="Choose cleaning team Duty")
    team_leader_id = fields.Many2one('hr.employee',
                                     string='Team Leader',
                                     help="Choose team leader")
    date_from = fields.Char(string='Cleaning Start Time',
                            help="Choose Cleaning Start Time", readonly=True)
    date_to = fields.Char(string='Cleaning End Date',
                          help="Choose Cleaning End Time", readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('cleaned', 'Cleaned'),
                              ('dirty', 'Dirty')
                              ], string='Status',
                             default='draft',
                             help="Inspection stages for cleaning")
    dirty_clean = fields.Boolean('Is Dirty or Clean',
                                 help="When the button is disabled,"
                                      " it signifies a Dirty state, "
                                      "while an enabled button signifies"
                                      " a Clean state.")

    def action_clean(self):
        """The button action for "Clean" involves executing a process
         to perform cleaning tasks"""
        self.write({'state': 'cleaned', 'dirty_clean': True})
        self.cleaning_id.write({'state': 'cleaned', 'clean_stage': True,
                                'cleaning_inspection_id': self.id})
        self.cleaning_team_duty_id.write(
            {'state': 'cleaned'})
        if not self.cleaning_id.cancel_stage:
            self.cleaning_id.cancel_stage = True

    def action_dirt(self):
        """The button action for "Dirty" typically
        involves marking task as dirty. """
        self.write({'state': 'dirty', 'dirty_clean': True})
        self.cleaning_team_duty_id.write(
            {'state': 'dirty'})

    def action_reclean(self):
        """Function for Reclean processes"""
        self.write({'state': 'draft'})
