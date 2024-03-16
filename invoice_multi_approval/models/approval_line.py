# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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


class ApprovalLine(models.Model):
    """This class creates a model 'approval.line' and adds fields"""
    _name = 'approval.line'
    _description = 'Approval Line In Move'

    move_id = fields.Many2one('account.move',
                              string="Approval lines", help="Approval line")
    approver_id = fields.Many2one('res.users', string='Approver',
                                  help="Approver of the invoice")
    approval_status = fields.Boolean(string='Status', help="Status of"
                                                           "approvals")
