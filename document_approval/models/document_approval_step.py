# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class DocumentApprovalSteps(models.Model):
    """ Document approval steps"""
    _name = "document.approval.step"
    _description = "Document Approvals Steps"

    steps = fields.Integer(string="Steps",
                           help="Number of steps required for the approval process.")
    approver_id = fields.Many2one('res.users', string="Approver",
                                  help="User responsible for approving the document."
                                  )
    role = fields.Char(string="Role/Position",
                       help="Position or role of the approver in the approval workflow.")
    document_approve_id = fields.Many2one('document.approval',
                                          string='Document Approval',
                                          help='Inverse field from document '
                                               'approvals')
    is_approve = fields.Boolean(string='Is Approved', copy=False,
                                help="Indicates whether the document has been approved.")
    document_approve_team_id = fields.Many2one('document.approval.team',
                                               string="Approver Team",
                                               help="Team responsible for handling the approval.")
    state = fields.Selection(
        selection=[('to_approve', 'To Approve'),
                   ('approve', 'Approve')],
        string="Status",
        default="to_approve",help="Indicates the approval status of this step. ")
    note = fields.Char(string='Notes', help="To add notes")
    current_state = fields.Selection(
        selection=[('upcoming', 'Upcoming'), ('pending', 'Pending'),
                   ('approved', 'Approved'), ('rejected', 'Rejected')],
        default="upcoming", string="Approval State",
        help="The current state of approval")
