# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Sreeshanth V S(<https://www.cybrosys.com>)
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


class DocumentApprovalSteps(models.Model):
    """ Document approval steps"""
    _name = "document.approval.step"
    _description = "Document Approvals Steps"

    steps = fields.Integer(string="Steps",
                           help='For counting how many steps needed')
    approver_id = fields.Many2one('res.users', string="Approver",
                                  help='The person who is responsible for '
                                       'the approval')
    role = fields.Char(string="Role/Position",
                       help='To determine the position of the approver')
    document_approve_id = fields.Many2one('document.approval',
                                          string='Document Approval',
                                          help='Inverse field from document '
                                               'approvals')
    is_approve = fields.Boolean(help='Check weather it is approved or not')
    document_approve_team_id = fields.Many2one('document.approval.team',
                                               string="Approver Team",
                                               help='The team who are '
                                                    'responsible for the '
                                                    'approvals')
    state = fields.Selection(
        selection=[('to_approve', 'To Approve'),
                   ('approve', 'Approve')],
        default="to_approve")
    note = fields.Char(string='Notes', help="To add notes")
    current_state = fields.Selection(
        selection=[('upcoming', 'Upcoming'), ('pending', 'Pending'),
                   ('approved', 'Approved'), ('rejected', 'rejected')],
        default="upcoming", string="Approval State",
        help="THe current state of approval")
