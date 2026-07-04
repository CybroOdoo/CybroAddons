# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class MaterialUsed(models.Model):
    """Model for material used in car workshop """
    _name = 'material.used'
    _description = 'Material Used in Car Workshop'

    material_product_id = fields.Many2one('product.product',
                                          string='Products',required=True,
                                          help="Product used for work")
    company_id = fields.Many2one('res.company', string='Company',
                                 help='The company of material',required=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(string='Company Currency',readonly=True,
                                  related='company_id.currency_id',
                                  help='The currency of the company')
    quantity = fields.Integer(string='Quantity', help='Amount for material used', default=1)
    price = fields.Monetary(string='Unit Price', help='Unit price for material')
    material_id = fields.Many2one('car.workshop', string='Material',
                                  help='The work details of material')
    invoice_line_ids = fields.Many2many('account.move.line', 'material_used_inv_line_rel', 'material_id', 'line_id', string='Invoice Lines')
    is_invoiced = fields.Boolean(string="Invoiced", compute='_compute_is_invoiced', store=True)

    @api.depends('invoice_line_ids.move_id.state')
    def _compute_is_invoiced(self):
        for rec in self:
            rec.is_invoiced = any(line.move_id.state != 'cancel' for line in rec.invoice_line_ids)

    @api.onchange('material_product_id')
    def _onchange_material_product_id(self):
        """ Function for update total price"""
        self.price = self.material_product_id.lst_price
