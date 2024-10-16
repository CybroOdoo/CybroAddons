# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, Command


class SaleTenderCreateAlternative(models.TransientModel):
    """"Creating module for wizard from alternative create confirmation"""
    _name = 'sale.tender.create.alternative'
    _description = 'Wizard to preset values for alternative PO'

    origin_so_id = fields.Many2one(
        'sale.order', help="The original PO that this alternative PO is being created for."
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        help="Choose a customer for alternative sO")

    copy_products = fields.Boolean(
        "Copy Products", default=True,
        help="If this is checked, the product quantities of the original sO will be copied")

    def action_create_alternative(self):
        """"Function to create alternative orders."""
        vals = self._get_alternative_values()
        alt_so = self.env['sale.order'].with_context(origin_so_id=self.origin_so_id.id, default_tender_id=False).create(vals)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': alt_so.id,
            'context': {
                'active_id': alt_so.id,
            },
        }

    def _get_alternative_values(self):
        """"function to return alternative values."""
        vals = {
            'date_order': self.origin_so_id.date_order,
            'partner_id': self.partner_id.id,
            'user_id': self.origin_so_id.user_id.id,
            'origin': self.origin_so_id.origin,
        }
        if self.copy_products and self.origin_so_id:
            vals['order_line'] = [Command.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'display_type': line.display_type,
                'name': line.name,
            }) for line in self.origin_so_id.order_line]
        return vals
