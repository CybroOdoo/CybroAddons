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


class AccountPaymentRegister(models.TransientModel):
    """Alter loan repayment line state based on invoice status"""
    _inherit = 'account.payment.register'

    def _post_payments(self, to_process, edit_mode=False):
        """Change repayment record state to 'paid' while registering the
        payment"""
        res = super()._post_payments(to_process, edit_mode=edit_mode)
        lines = self.env['repayment.line']
        for vals in to_process:
            for line in vals.get('to_reconcile', []):
                if line.move_id.repayment_line_id:
                    lines |= line.move_id.repayment_line_id
            batch = vals.get('batch', {})
            for line in batch.get('lines', []):
                if line.move_id.repayment_line_id:
                    lines |= line.move_id.repayment_line_id
        for record in self:
            for line in getattr(record, 'line_ids', []):
                if line.move_id.repayment_line_id:
                    lines |= line.move_id.repayment_line_id
            if record.communication:
                lines |= self.env['repayment.line'].search([
                    ('name', '=', record.communication)])
        if lines:
            lines.write({'state': 'paid'})
        return res

