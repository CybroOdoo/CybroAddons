# -*- coding: utf-8 -*-
###################################################################################
#    Job Card
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
    _name = "material.requisition"
    _description = "Material Requisition"

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', required=True)
    department_id = fields.Many2one('hr.department', required=True)
    date = fields.Date('Requisition Date')
    job_card_id = fields.Many2one('job.card')
    line_ids = fields.One2many('material.requisition.line', 'line_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submit'), ('approve', 'Approve'),
         ('po', 'Purchase Order')], default='draft')

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
                    'You cant submit the job card without instruction lines')
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
                    'order_line': lines
                })
                rec.state = 'po'


class MaterialRequisitionLine(models.Model):
    _name = "material.requisition.line"
    _description = 'Material Requisition Line'

    line_id = fields.Many2one("material.requisition")
    name = fields.Char()
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(required=True)
    uom = fields.Many2one('uom.uom')
    vendor_id = fields.Many2one('res.partner', required=True)
