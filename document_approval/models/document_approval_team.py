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
from odoo import fields, models


class DocumentApprovalTeam(models.Model):
    """ Configure document approval team"""
    _name = "document.approval.team"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Document approval team"

    name = fields.Char(string='Name', required=True, help='Name of the team',
                       tracking=True)
    team_lead_id = fields.Many2one('res.users', string='Team Leader',
                                   help='For setting th team lead',
                                   tracking=True, required=True,
                                   default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company',
                                 help='For setting the company',
                                 default=lambda self: self.env.company)
    is_active = fields.Boolean(string="Active",
                               help='For checking the active status')
    step_ids = fields.One2many('document.approval.step',
                               'document_approve_team_id',
                               help='For setting document approval steps for '
                                    'the approval team')
