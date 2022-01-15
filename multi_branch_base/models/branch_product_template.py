# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """inherited product"""
    _inherit = 'product.template'



    branch_id = fields.Many2one("res.branch", string='Branch', store=True,
                                readonly=False,
                                compute="_compute_branch")

    @api.depends('company_id')
    def _compute_branch(self):
        for order in self:
            company = self.env.company
            so_company = order.company_id if order.company_id else self.env.company
            branch_ids = self.env.user.branch_ids
            branch = branch_ids.filtered(
                lambda branch: branch.company_id == so_company)
            if branch:
                order.branch_id = branch.ids[0]
            else:
                order.branch_id = False
