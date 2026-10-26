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
from odoo import models, fields, api


class AccountMove(models.Model):
    """Alter loan repayment line state on draft and cancel button click"""
    _inherit = 'account.move'

    repayment_line_id = fields.Many2one('repayment.line', string="Repayment Line")

    def button_draft(self):
        """Change repayment record state to 'invoiced'
        while reset to draft the invoice"""
        res = super().button_draft()
        for record in self:
            line = record.repayment_line_id or (
                record.payment_reference and self.env['repayment.line'].search([
                    ('name', '=', record.payment_reference)], limit=1)
            )
            if line:
                line.write({
                    'state': 'invoiced',
                    'invoice': True,
                })
        return res

    def button_cancel(self):
        """Change repayment record state to 'unpaid'
        while cancelling the invoice"""
        res = super().button_cancel()
        for record in self:
            line = record.repayment_line_id or (
                record.payment_reference and self.env['repayment.line'].search([
                    ('name', '=', record.payment_reference)], limit=1)
            )
            if line:
                line.write({
                    'state': 'unpaid',
                    'invoice': False,
                })
        return res

    def _compute_payment_state(self):
        super()._compute_payment_state()
        for record in self:
            if record.payment_state in ['paid','reversed'] and record.repayment_line_id:
                if record.repayment_line_id.state != 'paid':
                    record.repayment_line_id.write({'state': 'paid'})




