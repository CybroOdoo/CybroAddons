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


class IdeaType(models.Model):
    """This class helps to create idea types by HR officer"""
    _name = 'idea.type'
    _inherit = 'mail.thread'
    _description = 'Idea Type'

    name = fields.Char(string="Name", help='Enter the name of Idea Type',
                       required=True)
    minimum_vote = fields.Integer(string="Minimum Vote",
                                  help='Specify the number of minimum vote'
                                       ' that this idea type should acquire',
                                  required=True, default=1)
    employee_ideas_id = fields.Many2one('employee.idea', string='Employee Idea',
                                        help='Connect with the model '
                                             'employee.idea and calculate '
                                             'total number of ideas')
    total_ideas = fields.Integer(string="Total ideas",
                                 compute='_compute_total_ideas',
                                 help='Shows the total number of ideas'
                                      'generated under this idea type')
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 help='Shows the current company')
    hr_department_ids = fields.Many2many('hr.department', string='Department',
                                         help='Shows the allowed departments '
                                              'under each idea type')

    def _compute_total_ideas(self):
        """This function is used to calculate the total number of idea
        created under this Idea Type"""
        for rec in self:
            rec.total_ideas = self.employee_ideas_id.search_count(
                [('idea_type_id', '=', self.id)]
            )

    def action_get_the_ideas(self):
        """This function is used to return the tree view of created ideas,
        while clicking the smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Ideas',
            'view_mode': 'tree',
            'res_model': 'employee.idea',
            'target': 'current',
            'domain': [('idea_type_id', '=', self.id)],
            'context': {"create": False}
        }
