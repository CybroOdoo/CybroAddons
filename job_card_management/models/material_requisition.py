# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo.exceptions import ValidationError

from odoo import models, fields, api


class MaterialRequisition(models.Model):
    _name = "material.requisition"
    _description = "Material Requisition"

    name = fields.Char('Name', help='Name')
    employee_id = fields.Many2one('hr.employee','Employee',
                                  required=True, help='Employee ID')
    department_id = fields.Many2one('hr.department',
                                    'Department', required=True,
                                    help='Department')
    date = fields.Date('Requisition Date', help='Date')
    job_card_id = fields.Many2one('job.card', 'Job Card',
                                  help='Job Card')
    line_ids = fields.One2many('material.requisition.line',
                               'line_id', 'Line Ids',
                               help='Line IDs')
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submit'), ('approve', 'Approve'),
         ('po', 'Purchase Order')], default='draft', string='State')

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

    line_id = fields.Many2one("material.requisition", 'Line ID', help='Line ID')
    name = fields.Char('Name', help='Name')
    product_id = fields.Many2one('product.product',string='Product', required=True, help='product')
    quantity = fields.Float(required=True, string='Quantity', help='Quantity')
    uom = fields.Many2one('uom.uom', 'Units of Measure', help='Units of measure')
    vendor_id = fields.Many2one('res.partner','Vendor', required=True, help='Vendor')
