# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Chethana Ramachandran (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Inherited Employee model"""
    _inherit = 'hr.employee'

    @api.depends()
    def _compute_allowed_branch_ids(self):
        """Compute the Allowed Branch"""
        for rec in self:
            rec.allowed_branch_ids = self.env.user.branch_ids.ids

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Trigger the compute function of allowed branch"""
        self._compute_allowed_branch_ids()

    allowed_branch_ids = fields.Many2many('res.branch',
                                          string="Allowed Branches",
                                          compute='_compute_allowed_branch_ids',
                                          help="List of all allowed branches")
    branch_id = fields.Many2one("res.branch", string='Branch',
                                help="Used to register the branch for the "
                                     "employee")
