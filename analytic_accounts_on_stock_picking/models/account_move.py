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
from odoo import models


class AccountMove(models.Model):
    """This class inherit the model 'account.move' and super the function
     'action post' to have the details of current transfer """
    _inherit = 'account.move'

    def action_post(self):
        """This function is used to add the transfer reference to the model
        'account.analytic.line' """
        res = super().action_post()
        origins = set(self.filtered('invoice_origin').mapped('invoice_origin'))
        if not origins:
            return res

        pickings = self.env['stock.picking'].search(
            [('origin', 'in', list(origins))],
            order='create_date desc, id desc',
        )
        picking_by_origin = {}
        for picking in pickings:
            picking_by_origin.setdefault(picking.origin, picking.name)

        invoice_lines = self.env['account.move.line'].search([
            ('move_id', 'in', self.filtered('invoice_origin').ids),
            ('display_type', '=', 'product'),
        ])
        analytic_lines = self.env['account.analytic.line'].search([
            ('move_line_id', 'in', invoice_lines.ids),
        ])
        lines_by_reference = {}
        for analytic_line in analytic_lines:
            invoice = analytic_line.move_line_id.move_id
            transfer_reference = picking_by_origin.get(invoice.invoice_origin)
            if transfer_reference:
                lines_by_reference.setdefault(transfer_reference, self.env[
                    'account.analytic.line'
                ])
                lines_by_reference[transfer_reference] |= analytic_line
        for transfer_reference, lines in lines_by_reference.items():
            lines.write({'transfer_reference': transfer_reference})
        return res
