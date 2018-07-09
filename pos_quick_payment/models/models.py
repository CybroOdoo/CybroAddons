# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosSessionQuickPayment(models.Model):
    _inherit = 'pos.config'

    quick_payment = fields.Boolean(string='Quick Payment')
    payment_options = fields.Many2many('pos.quick.payment', string='Payment Options')
    quick_payment_journal = fields.Many2one('account.journal', string='Payment Journal')

    @api.model
    def create(self, vals):
        if 'quick_payment' in vals and vals['quick_payment']:
            if 'quick_payment_journal' not in vals:
                raise UserError(_('Please configure journal for quick payment.'))
        return super(PosSessionQuickPayment, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'quick_payment' in vals and vals['quick_payment']:
            if 'quick_payment_journal' not in vals:
                raise UserError(_('Please configure journal for quick payment.'))
        return super(PosSessionQuickPayment, self).write(vals)


class PosQuickPayment(models.Model):
    _name = 'pos.quick.payment'

    name = fields.Char(string='Amount')
    note = fields.Text(string='Note')
