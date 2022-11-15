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

from odoo import models, fields, api, _
from odoo import exceptions
from odoo.exceptions import UserError


class ResUsers(models.Model):
    """inherited res users"""
    _inherit = "res.users"

    branch_ids = fields.Many2many('res.branch', string='Allowed Branches',
                                  domain="[('company_id', '=', company_ids)]")
    branch_id = fields.Many2one("res.branch", string='Default Branch',
                                default=False,
                                domain="[('id', '=', branch_ids)]")

    @api.constrains('branch_id')
    def branch_constrains(self):
        """branch constrains"""
        company = self.env.company
        for user in self:
            if user.branch_id and user.branch_id.company_id != company:
                raise exceptions.UserError(_("Sorry! The selected Branch does "
                                             "not belong to the current Company"
                                             " '%s'", company.name))

    def _get_default_warehouse_id(self):
        """methode to get default warehouse id"""
        if self.property_warehouse_id:
            return self.property_warehouse_id
        # !!! Any change to the following search domain should probably
        # be also applied in sale_stock/models/sale_order.py/_init_column.
        if len(self.env.user.branch_ids) == 1:
            warehouse = self.env['stock.warehouse'].search([
                ('branch_id', '=', self.env.user.branch_id.id)], limit=1)
            if not warehouse:
                warehouse = self.env['stock.warehouse'].search([
                    ('branch_id', '=', False)], limit=1)
            if not warehouse:
                error_msg = _(
                    "No warehouse could be found in the '%s' branch",
                    self.env.user.branch_id.name
                )
                raise UserError(error_msg)
            return warehouse
        else:
            return self.env['stock.warehouse'].search([
                ('company_id', '=', self.env.company.id)], limit=1)
