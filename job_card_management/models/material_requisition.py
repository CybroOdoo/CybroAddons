# -*- coding: utf-8 -*-
###################################################################################
#    Job Card Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Manasa T P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.exceptions import ValidationError

from odoo import models, fields, api


class MaterialRequisition(models.Model):
    """Create new model material requisition"""
    _name = "material.requisition"
    _description = "Material Requisition"

    name = fields.Char(
        string='Requisition Number',
        help='Unique reference number for the material requisition, automatically generated.'
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Requested By',
        required=True,
        help='The employee who requested this material requisition.'
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        required=True,
        help='The department requesting the materials.'
    )
    date = fields.Date(
        string='Requisition Date',
        default=fields.Date.today(),
        help='The date when the material requisition was created.'
    )
    job_card_id = fields.Many2one(
        comodel_name='job.card',
        string='Job Card',
        help='The job card associated with this material requisition.'
    )
    line_ids = fields.One2many(
        comodel_name='material.requisition.line',
        inverse_name='line_id',
        string='Requisition Lines',
        help='List of material items requested in this requisition.'
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submit', 'Submitted'),
            ('approve', 'Approved'),
            ('po', 'Purchase Order')
        ],
        string='Status',
        default='draft',
        help='Current status of the material requisition.'
    )
    purchase_order_count = fields.Integer(
        string="Purchase Orders",
        compute="_compute_purchase_order_count"
    )

    @api.model
    def create(self, vals_list):
        """create sequence"""
        sequence_code = 'material.requisition.sequence'
        vals_list['name'] = self.env['ir.sequence'].next_by_code(sequence_code)
        res = super(MaterialRequisition, self).create(vals_list)
        return res

    def action_submit(self):
        """submit button"""
        for rec in self:
            if not rec.line_ids.ids:
                raise ValidationError(
                    'You cant submit the Material Requisition without requisition lines')
            else:
                rec.state = 'submit'

    def action_approve(self):
        """approve button"""
        for rec in self:
            rec.state = 'approve'

    def create_purchase_order(self):
        """create purchase order"""
        for rec in self:
            lines = []
            for line in rec.line_ids:
                value = (0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'price_unit': line.product_id.standard_price,
                    'product_qty': line.quantity
                })
                lines.append(value)
                self.env['purchase.order'].create({
                    'partner_id': line.vendor_id.id,
                    'order_line': lines,
                    'material_requisition_id': rec.id,
                })
                rec.state = 'po'

    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = self.env[
                'purchase.order'].search_count([
                ('material_requisition_id', '=', rec.id)
            ])

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('material_requisition_id', '=', self.id)],
            'context': {'create': False}
        }


class MaterialRequisitionLine(models.Model):
    _name = "material.requisition.line"
    _description = 'Material Requisition Line'

    line_id = fields.Many2one(
        comodel_name='material.requisition',
        string='Material Requisition',
        help='The material requisition this line belongs to.'
    )
    name = fields.Char(
        string='Description',
        help='A brief description of the requisition line.'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        help='The product or material being requested.'
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        help='The quantity of the product requested.'
    )
    uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        help='The unit of measure for the requested product.'
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True,
        help='The vendor from whom the product will be purchased.'
    )
