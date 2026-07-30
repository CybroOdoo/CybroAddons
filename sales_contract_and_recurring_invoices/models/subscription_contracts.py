# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models
from odoo.tools import date_utils


class SubscriptionContracts(models.Model):
    """ Model for subscription contracts """
    _name = 'subscription.contracts'
    _description = 'Subscription Contracts'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Contract Name', required=True,
                       help='Name of Contract')
    reference = fields.Char(string='Reference', help='Contract reference')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help='Customer for this contract')
    recurring_period = fields.Integer(string='Recurring Period',
                                      help='Recurring period of '
                                           'subscription contract')
    recurring_period_interval = fields.Selection([
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('Months', 'Months'),
        ('Years', 'Years'),
    ], help='Recurring interval of subscription contract')
    contract_reminder = fields.Integer(
        string='Contract Expiration Reminder (Days)',
        help='Expiry reminder of subscription contract in days.')
    recurring_invoice = fields.Integer(
        string='Recurring Invoice Interval (Days)',
        help='Recurring invoice interval in days')
    next_invoice_date = fields.Date(string='Next Invoice Date', store=True,
                                    compute='_compute_next_invoice_date',
                                    readonly=False,
                                    help='Date of next invoice')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        required=True, default=lambda self: self.env.company.currency_id)
    date_start = fields.Date(string='Start Date', default=fields.Date.today(),
                             help='Subscription contract start date')
    invoice_count = fields.Integer(store=True,
                                   compute='_compute_invoice_count',
                                   string='Invoice count',
                                   help='Number of invoices generated')
    date_end = fields.Date(string='End Date', store=True,
                           compute='_compute_date_end', readonly=False,
                           help='Subscription End Date')
    current_reference = fields.Integer(compute='_compute_sale_order_lines',
                                       string='Current Subscription Id',
                                       help='Current Subscription id')
    lock = fields.Boolean(string='Lock', default=False,
                          help='Lock subscription contract so that further'
                               ' modifications are not possible.')
    state = fields.Selection([
        ('New', 'New'),
        ('Ongoing', 'Ongoing'),
        ('Expire Soon', 'Expire Soon'),
        ('Expired', 'Expired'),
        ('Cancelled', 'Cancelled'),
    ], string='Stage', default='New', copy=False, tracking=True,
        readonly=True, help='Status of subscription contract')
    contract_line_ids = fields.One2many(
        'subscription.contracts.line',
        'subscription_contract_id',
        string='Contract lines', help='Products to be added in the contract')
    amount_total = fields.Monetary(string="Total", store=True,
                                   compute='_compute_amount_total', tracking=4,
                                   help='Total amount')
    sale_order_line_ids = fields.One2many(
        'sale.order.line', 'contract_id',
        string='Sale Order Lines',
        help='Order lines of Sale Orders which belongs to this contract')
    invoice_ids = fields.One2many(
        'account.move', 'contract_origin', string='Invoices',
        help='Invoices generated from this contract')
    note = fields.Html(string="Terms and conditions",
                       help='Add any notes', translate=True)
    invoices_active = fields.Boolean(
        'Invoice active', default=False,
        compute='_compute_invoice_active',
        help='Compute invoices are active or not')

    generate_invoice_button = fields.Boolean(string='Generate Invoice button visibility',
                                             default=False, help='Generate invoice button visibility')

    def action_to_confirm(self):
        """ Confirm the Contract """
        self.write({'state': 'Ongoing'})

    def action_to_cancel(self):
        """ Cancel the Contract """
        self.write({'state': 'Cancelled'})

    # Fields whose change can affect the lifecycle state.
    _LIFECYCLE_TRIGGER_FIELDS = {
        'state', 'date_start', 'date_end', 'contract_reminder',
        'recurring_period', 'recurring_period_interval',
    }

    def _update_lifecycle_state(self):
        """ Move a confirmed contract among Ongoing / Expire Soon / Expired
        based on the current date and the *settled* end date. Never touches
        New or Cancelled contracts, so this can safely be called from both
        the cron and on save. """
        today = fields.Date.today()
        for rec in self:
            if rec.state in ('New', 'Cancelled') or not rec.date_end:
                continue
            warning_date = date_utils.subtract(
                rec.date_end, days=int(rec.contract_reminder))
            if rec.date_end < today:
                new_state = 'Expired'
            elif warning_date <= today <= rec.date_end:
                new_state = 'Expire Soon'
            else:
                new_state = 'Ongoing'
            if rec.state != new_state:
                rec.with_context(skip_lifecycle_update=True).state = new_state

    @api.model_create_multi
    def create(self, vals_list):
        """ Set the correct lifecycle state on creation """
        records = super().create(vals_list)
        records._update_lifecycle_state()
        return records

    def write(self, vals):
        """ Recompute the lifecycle state on save, after computed fields
        (such as date_end) have settled. The context guard prevents the
        state write inside the helper from recursing. """
        res = super().write(vals)
        if (not self.env.context.get('skip_lifecycle_update')
                and self._LIFECYCLE_TRIGGER_FIELDS & set(vals)):
            self._update_lifecycle_state()
        return res

    def _prepare_invoice_line_vals(self):
        """ Build invoice line command list from the contract lines """
        return [(0, 0, {
            'product_id': line.product_id.id,
            'name': line.description,
            'quantity': line.qty_ordered,
            'price_unit': line.price_unit,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
            'discount': line.discount,
        }) for line in self.contract_line_ids]

    def _create_contract_invoice(self):
        """ Create a customer invoice for the contract and advance the
        next invoice date by the recurring invoice interval """
        self.ensure_one()
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'currency_id': self.currency_id.id,
            'contract_origin': self.id,
            'invoice_line_ids': self._prepare_invoice_line_vals(),
        })
        if self.next_invoice_date:
            self.next_invoice_date = date_utils.add(
                self.next_invoice_date, days=int(self.recurring_invoice))
        return invoice

    def action_generate_invoice(self):
        """ Generate invoice """
        self._create_contract_invoice()
        self.generate_invoice_button = True

    def action_lock(self):
        """ Lock subscription contract """
        self.lock = True

    def action_to_unlock(self):
        """ Unlock subscription contract """
        self.lock = False

    def action_get_invoice(self):
        """ Access generated invoices """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('contract_origin', '=', self.id)],
        }

    @api.depends('contract_line_ids.sub_total')
    def _compute_amount_total(self):
        """ Compute total amount of Contract """
        for order in self:
            order_lines = order.contract_line_ids
            order.amount_total = sum(order_lines.mapped('sub_total'))

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        """ Compute the count of invoices generated """
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_active(self):
        """ Check invoice count to display the invoice smart button """
        for rec in self:
            rec.invoices_active = bool(rec.invoice_ids)

    @api.depends('date_start', 'recurring_invoice')
    def _compute_next_invoice_date(self):
        """ Compute the initial next invoice date of the contract.
        After an invoice is generated this value is advanced in code. """
        for rec in self:
            if rec.date_start:
                rec.next_invoice_date = date_utils.add(
                    rec.date_start, days=int(rec.recurring_invoice))
            else:
                rec.next_invoice_date = fields.Date.today()

    @api.depends('date_start', 'recurring_period', 'recurring_period_interval')
    def _compute_date_end(self):
        """ Compute contract end date from start date and recurring period """
        for rec in self:
            if not rec.date_start:
                rec.date_end = False
                continue
            recurring_period = int(rec.recurring_period)
            interval = rec.recurring_period_interval
            if interval == 'Weeks':
                rec.date_end = date_utils.add(rec.date_start,
                                              weeks=recurring_period)
            elif interval == 'Months':
                rec.date_end = date_utils.add(rec.date_start,
                                              months=recurring_period)
            elif interval == 'Years':
                rec.date_end = date_utils.add(rec.date_start,
                                              years=recurring_period)
            else:
                rec.date_end = date_utils.add(rec.date_start,
                                              days=recurring_period)

    @api.model
    def subscription_contract_state_change(self):
        """ Automatic state change and create invoice """
        current_date = fields.Date.today()
        records = self.env['subscription.contracts'].search([
            ('state', 'not in', ('New', 'Cancelled'))
        ])
        records._update_lifecycle_state()
        for rec in records:
            if (rec.next_invoice_date
                    and rec.next_invoice_date <= current_date
                    and rec.state in ('Ongoing', 'Expire Soon')):
                rec._create_contract_invoice()

    def _compute_sale_order_lines(self):
        """ Link existing sale order lines of the same partner/products
        within the contract period to this contract """
        for contract in self:
            contract.current_reference = contract.id
            if not (contract.partner_id and contract.date_start
                    and contract.date_end):
                continue
            products = contract.contract_line_ids.mapped('product_id')
            if not products:
                continue
            sale_order_lines = self.env['sale.order.line'].search([
                ('order_partner_id', '=', contract.partner_id.id),
                ('product_id', 'in', products.ids),
                ('create_date', '>=', contract.date_start),
                ('create_date', '<=', contract.date_end),
            ])
            sale_order_lines.contract_id = contract.id
