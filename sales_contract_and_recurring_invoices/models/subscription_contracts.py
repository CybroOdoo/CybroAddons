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
from odoo import api, fields, models
from odoo.tools import date_utils


class SubscriptionContracts(models.Model):
    """ Model for subscription contracts """
    _name = 'subscription.contracts'
    _description = 'Subscription Contracts'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Contract Name', required=True,
                       help='Name of Contract')
    reference = fields.Char(help='Contract reference')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help='Customer for this contract')
    recurring_period = fields.Integer(
        help='Recurring period of subscription contract'
    )
    recurring_period_interval = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Recurring Interval',
        help='Recurring interval of subscription contract')
    contract_reminder = fields.Integer(
        string='Contract Expiration Reminder (Days)',
        help='Expiry reminder of subscription contract in days.')
    recurring_invoice = fields.Integer(
        string='Recurring Invoice Interval (Days)',
        help='Recurring invoice interval in days')
    next_invoice_date = fields.Date(
        store=True,
        readonly=False,
        compute='_compute_next_invoice_date',
        help='Date of next invoice',
    )
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency',
        required=True, default=lambda self: self.env.company.currency_id)
    date_start = fields.Date(string='Start Date', default=fields.Date.today,
                             help='Subscription contract start date')
    invoice_ids = fields.One2many(
        'account.move', 'contract_origin_id', string='Invoices',
        help='Invoices generated for this contract')
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   help='Number of invoices generated')
    date_end = fields.Date(compute='_compute_next_invoice_date',
                           store=True, readonly=False,
                           help='Subscription End Date')

    lock = fields.Boolean(default=False,
                          help='Lock subscription contract so that further'
                               ' modifications are not possible.')
    state = fields.Selection([
        ('new', 'New'),
        ('ongoing', 'Ongoing'),
        ('expire_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Stage', default='new', copy=False, tracking=True,
        readonly=True, help='Status of subscription contract')
    contract_line_ids = fields.One2many(
        'subscription.contracts.line',
        'subscription_contract_id',
        string='Contract lines', help='Products to be added in the contract')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     compute='_compute_amount_all')
    amount_tax = fields.Monetary(string='Taxes', store=True,
                                 compute='_compute_amount_all')
    amount_total = fields.Monetary(string="Total", store=True,
                                   compute='_compute_amount_all', tracking=4,
                                   help='Total amount')
    sale_order_line_ids = fields.One2many(
        'sale.order.line', 'contract_id',
        string='Sale Order Lines',
        help='Order lines of Sale Orders which belongs to this contract')
    note = fields.Html(string="Terms and conditions",
                       help='Add any notes', translate=True)
    invoices_active = fields.Boolean(
        'Invoice active', default=False,
        compute='_compute_invoice_active',
        help='Compute invoices are active or not')

    def action_to_confirm(self):
        """ Confirm the Contract """
        self.write({'state': 'ongoing'})

    def action_to_cancel(self):
        """ Cancel the Contract """
        self.write({'state': 'cancelled'})

    def action_lock(self):
        """ Lock subscription contract """
        self.write({'lock': True})

    def action_to_unlock(self):
        """ Unlock subscription contract """
        self.write({'lock': False})

    def action_generate_invoice(self):
        """ Generate invoice """
        self.ensure_one()
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'contract_origin_id': self.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.display_name,
                    'quantity': line.qty_ordered,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': [fields.Command.set(line.tax_ids.ids)],
                }) for line in self.contract_line_ids
            ],
        })
        if self.recurring_invoice:
            self.next_invoice_date = date_utils.add(fields.Date.today(), days=int(self.recurring_invoice))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('contract_line_ids.price_subtotal', 'contract_line_ids.price_total')
    def _compute_amount_all(self):
        for contract in self:
            untaxed = sum(contract.contract_line_ids.mapped('price_subtotal'))
            total = sum(contract.contract_line_ids.mapped('price_total'))
            contract.amount_untaxed = untaxed
            contract.amount_total = total
            contract.amount_tax = total - untaxed

    def action_get_invoice(self):
        """ Access generated invoices """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('contract_origin_id', '=', self.id)],
        }

    def _get_report_base_filename(self):
        self.ensure_one()
        return f"Subscription Contract - {self.name}"

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        """ Compute the count of invoices generated """
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('invoice_count')
    def _compute_invoice_active(self):
        """ Check invoice count to display the invoice smart button """
        for rec in self:
            rec.invoices_active = rec.invoice_count > 0

    @api.depends('date_start', 'recurring_invoice', 'recurring_period',
                 'recurring_period_interval')
    def _compute_next_invoice_date(self):
        """ Compute next invoice date and end date of contract """
        for rec in self:
            start_date = rec.date_start or fields.Date.today()
            interval = rec.recurring_invoice or 0
            if not rec.next_invoice_date or (rec.state == 'new' and not rec.invoice_ids):
                rec.next_invoice_date = (
                    date_utils.add(start_date, days=int(interval)) if interval else start_date
                )

            recurring_period = int(rec.recurring_period or 0)
            if recurring_period:
                interval_type = rec.recurring_period_interval
                if interval_type == 'days':
                    rec.date_end = date_utils.add(start_date, days=recurring_period)
                elif interval_type == 'weeks':
                    rec.date_end = date_utils.add(start_date, weeks=recurring_period)
                elif interval_type == 'months':
                    rec.date_end = date_utils.add(start_date, months=recurring_period)
                elif interval_type == 'years':
                    rec.date_end = date_utils.add(start_date, years=recurring_period)
            else:
                rec.date_end = False

    @api.model
    def subscription_contract_state_change(self):
        """ Automatic state change and create invoice """
        current_date = fields.Date.today()
        records = self.search([
            ('state', 'in', ['ongoing', 'expire_soon']),
        ])
        for rec in records:
            end_date = rec.date_end
            if end_date:
                expiry_reminder = rec.contract_reminder or 0
                expiry_warning_date = date_utils.add(end_date, days=-int(expiry_reminder))

                if expiry_warning_date <= current_date <= end_date:
                    if rec.state != 'expire_soon':
                        rec.write({'state': 'expire_soon'})

                if end_date < current_date:
                    if rec.state != 'expired':
                        rec.write({'state': 'expired'})

            if (
                rec.next_invoice_date
                and rec.next_invoice_date <= current_date
                and rec.state not in ('cancelled', 'expired')
            ):
                rec.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.partner_id.id,
                    'invoice_date': current_date,
                    'contract_origin_id': rec.id,
                    'invoice_line_ids': [
                        fields.Command.create({
                            'product_id': line.product_id.id,
                            'name': line.description or line.product_id.display_name,
                            'quantity': line.qty_ordered,
                            'price_unit': line.price_unit,
                            'discount': line.discount,
                            'tax_ids': [fields.Command.set(line.tax_ids.ids)],
                        }) for line in rec.contract_line_ids
                    ],
                })

                if rec.recurring_invoice:
                    base_date = rec.next_invoice_date or current_date
                    next_schedule = date_utils.add(base_date, days=int(rec.recurring_invoice))
                    while next_schedule <= current_date:
                        next_schedule = date_utils.add(next_schedule, days=int(rec.recurring_invoice))
                    rec.write({'next_invoice_date': next_schedule})

