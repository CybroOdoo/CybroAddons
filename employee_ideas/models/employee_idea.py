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
from odoo import api, fields, models, _


class EmployeeIdeas(models.Model):
    """This class is used for creating ideas under the idea type"""
    _name = 'employee.idea'
    _description = 'Employee Ideas'
    _inherit = 'mail.thread'
    _rec_name = "reference_no"

    def get_employee_name(self):
        """This function is used to get the name of current employee"""
        employee_rec_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee_rec_id

    def get_idea_type_domain(self):
        """This function is used to get the idea types"""
        employee_rec_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        idea_type_list = []
        employee_dept = employee_rec_id.department_id
        idea_type_rec = self.idea_type_id.search([])
        for rec in idea_type_rec:
            department_rec = rec.hr_department_ids.ids
            if employee_dept.id in department_rec:
                idea_type_list.append(rec.id)
        return [('id', 'in', idea_type_list)]

    title = fields.Char(string="Title", help='Title of your idea',
                        required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help='Employee created the idea',
                                  default=get_employee_name)
    idea_type_id = fields.Many2one('idea.type', help='Idea type of the idea',
                                   domain=get_idea_type_domain,
                                   required=True)
    details = fields.Text(string="Details",
                          help='Enter the details of your idea', required=True)
    vote_count = fields.Integer(compute='_compute_vote_count', help='Shows the '
                                                                    'number of '
                                                                    'votes '
                                                                    'obtained')
    is_vote = fields.Boolean(string="Voted", compute='_compute_is_vote',
                             help='Shows whether the employee is voted or not')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('approval', 'Approval'),
                                        ('post', 'Posted'),
                                        ('rejected', 'Rejected')],
                             default='draft', help='Stages of ideas')
    reference_no = fields.Char(string='Order Reference', readonly=True,
                               copy=False, help='Sequence number',
                               default=lambda self: _('New'))
    employee_vote_ids = fields.One2many('give.vote', 'employee_ideas_id',
                                        string="Vote",
                                        help='Connect with the model give.vote '
                                             'to check the voting status of '
                                             'employee')
    have_minimum_vote = fields.Text(string='Status', help='This field shows, '
                                                          'that whether the '
                                                          'idea has minimum '
                                                          'vote or not')
    is_visible_give_vote = fields.Boolean(string='Visible Give Vote',
                                          compute='_compute_is_visible_give_vote',
                                          help='Check whether need to show'
                                               'the Give Vote button ')
    company_id = fields.Many2one('res.company', help='Company', readonly=True,
                                 default=lambda self: self.env.company)
    is_send_approval_visibility = fields.Boolean(string="send approval",
                                                 readonly=False,
                                                 compute='_compute_is_send_approval_visibility',
                                                 help='Check Whether, need to'
                                                      ' show the Send '
                                                      'Approval button for'
                                                      ' employee', store=True)

    @api.model
    def create(self, vals):
        """This function create the reference number"""
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'employee.idea') or _('New')
        res = super(EmployeeIdeas, self).create(vals)
        return res

    def _compute_is_send_approval_visibility(self):
        """This function is used to determine the visibility of send for
        approval button"""
        for rec in self:
            if rec.create_uid.id == self.env.user.id:
                rec.is_send_approval_visibility = True
            else:
                rec.is_send_approval_visibility = False

    def action_send_approval(self):
        """Change the state of a record in to Post"""
        self.write({'state': 'approval'})

    def action_approve(self):
        """Change the state of a record in to Approved"""
        self.write({'state': 'post'})

    def action_reject(self):
        """Change the state of a record in to Rejected"""
        self.write({'state': 'rejected'})

    def action_give_vote(self):
        """This function opens a wizard while click on 'Give Vote' button,
         where provides an interface to vote or to comment"""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)]
        )
        give_votes_rec = self.env['give.vote'].create({
            'employee_id': employee.id,
            'reference': self.reference_no,
            'employee_ideas_id': self.id
        })
        return {
            'name': 'Give Vote',
            'type': 'ir.actions.act_window',
            'res_model': 'give.vote',
            'view_mode': 'form',
            'res_id': give_votes_rec.id,
            'target': 'new'
        }

    def _compute_is_vote(self):
        """This function is used to allow an employee to do single vote"""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        self.is_vote = False
        for rec in self:
            vote_employee = rec.employee_vote_ids.search(
                [('reference', '=', rec.reference_no),
                 ('status', '=', 'Voted')])
            if not vote_employee:
                rec.is_vote = False
            else:
                for record in vote_employee:
                    if employee.id == record.employee_id.id:
                        rec.is_vote = True
                    else:
                        rec.is_vote = False

    def _compute_vote_count(self):
        """ This compute function used to count the number of votes get to a
        particular idea"""
        for rec in self:
            rec.vote_count = self.employee_vote_ids.search_count(
                [('employee_ideas_id', '=', self.id), ('is_vote', '=', 'True')])
        if self.vote_count >= self.idea_type_id.minimum_vote:
            self.have_minimum_vote = 'Go with this'
        else:
            self.have_minimum_vote = 'Does not have minimum vote'

    def _compute_is_visible_give_vote(self):
        """This function is used to make visible the Give Vote button only to
        the employees, who are in specified department"""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)]
        )
        for rec in self:
            rec.is_visible_give_vote = False
            if rec.create_uid.id == self.env.user.id:
                rec.is_visible_give_vote = False
                break
            department = rec.idea_type_id.hr_department_ids.ids
            if employee.department_id.id in department:
                rec.is_visible_give_vote = True

    def action_get_votes_of_idea(self):
        """This function is used to return the tree view showing the votes
        gained while clicking the smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Votes',
            'view_mode': 'tree',
            'res_model': 'give.vote',
            'target': 'current',
            'domain': [('employee_ideas_id', '=', self.id),
                       ('status', '=', 'Voted')],
            'context': {"create": False}
        }

    def action_get_comments_of_idea(self):
        """This function is used to return the tree view  showing the comments
       """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Comments',
            'view_mode': 'tree',
            'res_model': 'give.vote',
            'target': 'current',
            'domain': [('employee_ideas_id', '=', self.id),
                       ('status', '=', 'Commented')],
            'context': {"create": False}
        }

    def action_print(self):
        """This function is responsible for the printing pdf reports"""
        query = """
                select reference_no,hr_employee.name,title,details,
                employee_idea.state
                from employee_idea
                inner join hr_employee on employee_id=hr_employee.id
                where employee_idea.id = %s
                """ % self.id
        self.env.cr.execute(query)
        data = {
            'query_fetch': self.env.cr.dictfetchall(),
        }
        return self.env.ref(
            'employee_ideas.employee_idea_action_report').report_action(None,
                                                                        data=data)
