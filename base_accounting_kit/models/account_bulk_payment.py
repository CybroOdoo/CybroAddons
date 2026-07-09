# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountBulkPayment(models.Model):
    """Groups several customer/vendor payments (same journal, type and method)
    into one batch for bank processing/deposit."""
    _name = 'account.bulk.payment'
    _description = 'Bulk Payment'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    batch_type = fields.Selection(
        [('inbound', 'Inbound'), ('outbound', 'Outbound')],
        string='Type', required=True, default='inbound', tracking=True)
    journal_id = fields.Many2one(
        'account.journal', string='Bank', required=True, tracking=True,
        domain="[('type', 'in', ('bank', 'cash'))]")
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', string='Payment Method',
        domain="[('journal_id', '=', journal_id)]")
    date = fields.Date(string='Date', required=True,
                       default=fields.Date.context_today)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    payment_ids = fields.One2many('account.payment', 'bulk_payment_id',
                                  string='Payments')
    amount_total = fields.Monetary(compute='_compute_amount_total',
                                   store=True)
    payment_count = fields.Integer(compute='_compute_payment_count')
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')],
                             default='draft', copy=False, tracking=True)

    @api.depends('payment_ids.amount')
    def _compute_amount_total(self):
        for batch in self:
            batch.amount_total = sum(batch.payment_ids.mapped('amount'))

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for batch in self:
            batch.payment_count = len(batch.payment_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'account.bulk.payment') or _('New')
        return super().create(vals_list)

    @api.constrains('payment_ids', 'journal_id', 'batch_type',
                    'payment_method_line_id')
    def _check_payments_consistency(self):
        for batch in self:
            for pay in batch.payment_ids:
                if pay.journal_id != batch.journal_id:
                    raise ValidationError(_(
                        "All payments in the batch must use the journal %s.")
                        % batch.journal_id.display_name)
                if pay.payment_type != batch.batch_type:
                    raise ValidationError(_(
                        "All payments in the batch must be of type '%s'.")
                        % batch.batch_type)
                if batch.payment_method_line_id and \
                        pay.payment_method_line_id != batch.payment_method_line_id:
                    raise ValidationError(_(
                        "All payments must use the payment method %s.")
                        % batch.payment_method_line_id.display_name)

    def action_validate(self):
        """Post the draft payments of the batch, mark them sent and close it."""
        for batch in self:
            if not batch.payment_ids:
                raise ValidationError(_("Add at least one payment to the batch."))
            batch.payment_ids.filtered(
                lambda p: p.state == 'draft').action_post()
            batch.payment_ids.write({'is_sent': True})
            batch.state = 'sent'
        return True

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'base_accounting_kit.action_report_bulk_payment').report_action(self)

    def action_open_payments(self):
        self.ensure_one()
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.payment_ids.ids)],
        }
