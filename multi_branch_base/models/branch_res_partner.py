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


class BranchPartner(models.Model):
    """inherited partner"""
    _inherit = "res.partner"

    branch_id = fields.Many2one("res.branch", string='Branch', store=True,
                                help='Leave this field empty if the partner is'
                                     ' shared between all branches'
                                )
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Branches",
                                          compute='_compute_allowed_branch_ids')

    @api.depends('company_id')
    def _compute_allowed_branch_ids(self):
        for po in self:
            po.allowed_branch_ids = self.env.user.branch_ids.ids

    @api.model
    def default_get(self, default_fields):
        """Add the company of the parent as default if we are creating a
        child partner.Also take the parent lang by default if any, otherwise,
        fallback to default DB lang."""
        values = super().default_get(default_fields)
        parent = self.env["res.partner"]
        if 'parent_id' in default_fields and values.get('parent_id'):
            parent = self.browse(values.get('parent_id'))
            values['branch_id'] = parent.branch_id.id
        return values

    @api.onchange('parent_id', 'branch_id')
    def _onchange_parent_id(self):
        """methode to set branch on changing the parent company"""
        if self.parent_id:
            self.branch_id = self.parent_id.branch_id.id

    def write(self, vals):
        """override write methode"""
        if vals.get('branch_id'):
            branch_id = vals['branch_id']
            for partner in self:
                # if partner.child_ids:
                for child in partner.child_ids:
                    child.write({'branch_id': branch_id})
        else:
            for partner in self:
                # if partner.child_ids:
                for child in partner.child_ids:
                    child.write({'branch_id': False})
        result = super(BranchPartner, self).write(vals)
        return result
