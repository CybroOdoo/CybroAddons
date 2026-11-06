# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import _, Command, fields, models
from odoo.exceptions import UserError


class CommissionLines(models.Model):
    """Creating a commission lines model."""
    _name = "commission.lines"
    _description = "Commission Lines"
    _rec_name = "description"

    date = fields.Date(
        string="Date",
        help="Date on which the sales commission was recorded.",
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="Sale order associated with this commission line.",
    )
    description = fields.Char(
        string="Name",
        help="Description of the sales commission line.",
    )
    sales_person_id = fields.Many2one(
        'res.users',
        string='Sales Person',
        help="Salesperson receiving this commission.",
    )
    order_ref = fields.Char(
        string='Order Reference',
        help="Reference name of the sale order.",
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help="Customer associated with the sale order.",
    )
    commission = fields.Char(
        string='Commission Name',
        help="Name of the applied sales commission scheme.",
    )
    commission_type = fields.Selection(
        string="Commission Type",
        selection=[
            ('standard', 'Standard'),
            ('partner_based', 'Partner Based'),
            ('product_based', 'Product Based'),
            ('discount_based', 'Discount Based'),
        ],
        help="Type of commission calculation applied.",
    )
    commission_amount = fields.Float(
        string="Commission Amount",
        help="Amount of commission calculated for this line.",
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False,
        help="Invoice created for this commission line.",
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('invoiced', 'Invoiced'),
        ],
        default='draft',
        string='Status',
        help="Current status of the commission line.",
    )

    def action_create_invoice(self):
        """Creating invoice for sales commission."""
        if not self:
            return {}

        if any(rec.state == 'invoiced' for rec in self):
            raise UserError(
                _("One or more selected commission lines are already invoiced.")
            )

        partners = self.sales_person_id.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(_("Sales Person should be same."))

        partner = partners[:1]
        if not partner:
            raise UserError(
                _("The selected salesperson does not have a partner record.")
            )

        lines = [Command.create({
            'name': rec.description or _("Sales Commission"),
            'quantity': 1.0,
            'discount': 0.00,
            'price_unit': rec.commission_amount,
        }) for rec in self]

        order_refs = ', '.join(filter(None, set(self.mapped('order_ref'))))
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'payment_reference': order_refs or False,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': lines,
        })
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'domain': [('id', '=', invoice.id)],
            'context': {'create': False},
        }
