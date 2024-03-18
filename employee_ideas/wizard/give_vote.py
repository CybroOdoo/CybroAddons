# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import fields, models
from odoo.exceptions import ValidationError


class GiveVote(models.TransientModel):
    """This class is used to shows a popup, in that the employees are able to
    add their comments, and also they can submit their votes"""
    _name = 'give.vote'
    _description = "Give Votes"

    comments = fields.Text(string="Comments", help="Comments")
    employee_ideas_id = fields.Many2one('employee.idea', help='Connect the model'
                                                     ' employee.idea')
    reference = fields.Char(string="Reference", help='Reference of Idea')
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  readonly=True, help='Employee')
    employee_department_id = fields.Many2one(string='Department',
                                             related='employee_id.department_id',
                                             store=True, help='Department of'
                                                              ' the employee')
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'),
                                 ('3', 'Very High')], default='0',
                                index=True, string="Priority", tracking=True,
                                help='Priority of the idea')
    is_vote = fields.Boolean(string='Vote', help='Enable, when click on the '
                                                 'Give vote button')
    status = fields.Text(string="Status", help='Status of the idea')
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 help='Shows the current company')

    def action_vote(self):
        """This function changes the status of a record in to Voted,
         if any employee votes the idea"""
        self.is_vote = True
        self.status = 'Voted'
        if self.is_vote:
            self.employee_ideas_id.is_vote = True

    def action_submit_comment(self):
        """This function changes the status of a record in to Commented,
        if any employee comment the idea"""
        if not self.comments:
            raise ValidationError("Have a Comment")
        self.status = 'Commented'
