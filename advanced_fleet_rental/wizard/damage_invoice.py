# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class DamageInvoice(models.TransientModel):
    """
    This model handles the linking of invoices to sale orders.
    """
    _name = 'damage.invoice'
    _description = "Damage Report"

    is_damage = fields.Boolean(string="Any Damage",
                               help="The Vehicle is Damaged")
    damage_amount = fields.Float(string="Damage Amount",
                                 help="Total Amount for the damages")
    description = fields.Text(
        'Description', translate=True)
    contract_id = fields.Many2one(
        'fleet.rental.contract',
        string='Contract Rent',
        help='Reference to the vehicle rent.')

    def action_create_damage_invoice(self):
        """
        Creates an invoice for the reported damages based on the provided
        details.
        """
        self.ensure_one()
        if not self.contract_id:
            raise ValidationError(_("No contract associated with this damage report."))
        if not self.damage_amount:
            raise ValidationError(_("Damage amount is required to create an invoice."))

        product_id = self.env.ref(
            'advanced_fleet_rental.product_product_vehicle_damage_charge')
        invoice_vals = {
            'partner_id': self.contract_id.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'vehicle_rental_id': self.contract_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product_id.id,
                'name': self.description or '',
                'quantity': 1,
                'price_unit': self.damage_amount,
            })],
        }
        self.contract_id.is_damaged_invoiced = True
        self.contract_id.damage_description = self.description
        self.contract_id.damage_amount = self.damage_amount
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
