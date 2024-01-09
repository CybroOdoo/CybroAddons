# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Chethana Ramachandran(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Inherited Employee Model"""
    _inherit = 'hr.employee'

    branch_id = fields.Many2one("res.branch", string='Branch', store=True,
                                readonly=False,
                                compute="_compute_branch_id",
                                help="Used to register the branch for the "
                                     "employee")
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Allowed Branches",
                                          compute='_compute_branch_id',
                                          help="List of all allowed branches")

    @api.depends('company_id')
    def _compute_branch_id(self):
        """Compute the branch for the employee"""
        for rec in self:
            rec.allowed_branch_ids = self.env.user.branch_ids.ids
            company = rec.company_id if rec.company_id else self.env.company
            branch = self.env.user.branch_ids.filtered(
                lambda branch: branch.company_id == company)
            rec.branch_id = branch.ids[0] if branch else False
