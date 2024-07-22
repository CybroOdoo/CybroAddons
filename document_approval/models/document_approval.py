# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S(<https://www.cybrosys.com>)
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
from odoo.exceptions import UserError, ValidationError


class DocumentApproval(models.Model):
    """ Manage document approvals"""
    _name = "document.approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Document Approvals"

    name = fields.Char(string='Name', required=True, help='name of the record')
    is_active = fields.Boolean(string='Active',
                               help='Used to check the record active or not')
    description = fields.Text(string="Description",
                              help='Used to add description about the document'
                                   ' approval')
    approve_initiator_id = fields.Many2one('res.users', string="Initiator",
                                           default=lambda self: self.env.user,
                                           help='Set who has initiated the '
                                                'document approval')
    team_id = fields.Many2one('document.approval.team', string="Approval Team",
                              required=True,
                              help='Set which team is approving the document')
    method = fields.Selection(selection=[('button', 'Button'),
                                         ('sign', 'Signature')],
                              default='button', string="Method",
                              help='Set the mode of approvals')
    visibility = fields.Selection(selection=[('all_user', 'All Users'),
                                             ('followers', 'Followers'),
                                             ('approvers', 'Approvers')],
                                  string='Visibility',
                                  help='Restrict the visibility of the '
                                       'document', default="all_user")
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('waiting', 'Waiting'),
                                        ('approved', 'Approved'),
                                        ('reject', 'Rejected')],
                             string='Status', default='draft', readonly=True,
                             tracking=True,
                             help='State of the document')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Company of the record')
    step_ids = fields.One2many('document.approval.step',
                               'document_approve_id',
                               compute='_compute_step_ids', store=True,
                               help='For setting document approval steps')
    file_ids = fields.One2many('document.approval.file', 'approval_id',
                               string='Files',
                               help='You can upload file and file details')
    step_count = fields.Integer(string="Step", help="Current Step",
                                readonly=True)
    approver_ids = fields.Many2many('res.users', string="Approver",
                                    help="User to approve the document")
    show_approve = fields.Boolean(string="Show Approve Button",
                                  help="To show the approve button to approve "
                                       "the document",
                                  compute="_compute_show_approve")
    approval_ids = fields.Many2many('document.approval.step',
                                    string="Approval Step",
                                    help="Approval Step of the document")

    @api.depends('team_id')
    def _compute_step_ids(self):
        """Method _compute_step_ids to compute the values to the field
        step_ids"""
        for rec in self:
            rec.step_ids = False
            for step in rec.team_id.step_ids:
                rec.step_ids = [fields.Command.create({
                    'steps': step.steps,
                    'approver_id': step.approver_id.id,
                    'role': step.role,
                    'state': step.state,
                    'note': step.note
                })]

    @api.constrains('team_id')
    def _check_team_member(self):
        """function to check whether the team has atleast one member."""
        if not self.team_id.step_ids.approver_id:
            raise ValidationError(
                "Your Team member should atleast have one Approver.")

    @api.depends('team_id')
    def _compute_show_approve(self):
        """This method _compute_show_approve to compute the valur to the field
        show_approve"""
        for rec in self:
            rec.show_approve = True if self.env.uid in rec.approver_ids.ids else False
            if rec.team_id.team_lead_id.id == self.env.uid:
                rec.show_approve = True

    def action_send_for_approval(self):
        """ Action to sent document to approval also it changes the state
        into waiting that document to be approved """
        steps = self.step_ids.mapped('steps')
        unique_steps = []
        for step in steps:
            if step not in unique_steps:
                unique_steps.append(step)
        unique_steps = sorted(unique_steps)
        self.step_count = unique_steps[0]
        aprroval_records = self.step_ids.search([('steps', '=',
                                                  unique_steps[0]), (
                                                     'document_approve_id',
                                                     '=', self.id)])
        self.approval_ids = aprroval_records.ids
        approval_user_ids = []
        for record in aprroval_records:
            approval_user_ids.append(record.approver_id.id)
            record.current_state = 'pending'
        self.approver_ids = approval_user_ids
        self.state = "waiting"

    def action_approve(self):
        """ function that return wizard to do the approval by writing note
        and approver can approve the document.
        Approval is done just clicking the button"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Approval',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'document.approve',
            'context': {
                'default_document_id': self.id
            }
        }

    def action_reject(self):
        """ Return a wizard that to confirm rejection by adding a note"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Rejection',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'document.reject',
            'context': {
                'default_document_id': self.id
            }
        }

    def action_approve_sign(self):
        """ Return a wizard that approver can ensure to give
        signature and approve.Approver can add signature confirmation """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Approval',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'document.approval.signature',
            'context': {
                'default_document_id': self.id
            }
        }

    def unlink(self):
        """ This function is used to ensure to there is no record of
        state approved has been deleted"""
        for record in self:
            if record.state in ["approved", "waiting"]:
                raise UserError(
                    _("You cannot delete record in approved or waiting state"))
            return super(DocumentApproval, self).unlink()
