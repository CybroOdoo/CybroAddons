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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountRecurringInvoice(models.Model):
    """Template that periodically generates customer invoices or vendor bills
    on a fixed schedule (e.g. monthly retainers, rent, subscriptions)."""
    _name = 'account.recurring.invoice'
    _description = 'Recurring Invoice Template'
    _inherit = ['mail.thread']
    _order = 'date_next, id'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    move_type = fields.Selection(
        [('out_invoice', 'Customer Invoice'), ('in_invoice', 'Vendor Bill')],
        string='Document Type', required=True, default='out_invoice',
        tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True, tracking=True)
    journal_id = fields.Many2one(
        'account.journal', string='Journal',
        domain="[('type', '=', journal_type)]",
        help="Leave empty to use the default journal for the document type.")
    journal_type = fields.Char(compute='_compute_journal_type')
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    line_ids = fields.One2many(
        'account.recurring.invoice.line', 'recurring_id', string='Lines',
        copy=True)
    interval_number = fields.Integer(string='Repeat Every', default=1,
                                     required=True)
    interval_type = fields.Selection(
        [('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'),
         ('years', 'Years')], string='Period', default='months',
        required=True)
    date_start = fields.Date(
        string='Start Date', required=True, default=fields.Date.context_today)
    date_next = fields.Date(string='Next Invoice Date', readonly=True,
                            copy=False, tracking=True)
    date_end = fields.Date(string='End Date',
                           help="No invoices are generated past this date.")
    auto_post = fields.Boolean(
        string='Auto Post', default=False,
        help="Automatically post the generated invoices. When disabled the "
             "invoices are created as drafts for review.")
    state = fields.Selection(
        [('draft', 'Draft'), ('running', 'Running'), ('done', 'Done')],
        string='Status', default='draft', copy=False, tracking=True)
    invoice_ids = fields.One2many(
        'account.move', 'recurring_invoice_id', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    @api.depends('move_type')
    def _compute_journal_type(self):
        for rec in self:
            rec.journal_type = 'sale' if rec.move_type == 'out_invoice' \
                else 'purchase'

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.onchange('move_type')
    def _onchange_move_type(self):
        # A journal picked for the other document type is no longer valid.
        if self.journal_id and self.journal_id.type != self.journal_type:
            self.journal_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'account.recurring.invoice') or _('New')
        return super().create(vals_list)

    def _next_date(self, date):
        """Return ``date`` advanced by one recurrence interval."""
        self.ensure_one()
        return date + relativedelta(**{self.interval_type: self.interval_number})

    def action_start(self):
        """Activate the template so the cron starts generating invoices."""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("Add at least one line before starting '%s'.")
                                % rec.name)
            rec.write({
                'state': 'running',
                'date_next': rec.date_next or rec.date_start,
            })
        return True

    def action_stop(self):
        self.write({'state': 'done'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    def _create_invoice(self, invoice_date):
        """Create (and optionally post) one invoice for ``invoice_date``."""
        self.ensure_one()
        line_vals = []
        for line in self.line_ids:
            vals = {
                'product_id': line.product_id.id,
                'name': line.name or (line.product_id.display_name or ''),
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'tax_ids': [fields.Command.set(line.tax_ids.ids)],
            }
            if line.account_id:
                vals['account_id'] = line.account_id.id
            line_vals.append(fields.Command.create(vals))
        move_vals = {
            'move_type': self.move_type,
            'partner_id': self.partner_id.id,
            'invoice_date': invoice_date,
            'currency_id': self.currency_id.id,
            'recurring_invoice_id': self.id,
            'invoice_line_ids': line_vals,
        }
        if self.journal_id:
            move_vals['journal_id'] = self.journal_id.id
        move = self.env['account.move'].with_company(self.company_id).create(
            move_vals)
        if self.auto_post:
            move.action_post()
        return move

    def _generate_due(self):
        """Generate every invoice due up to today and advance the schedule."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        moves = self.env['account.move']
        # Cap iterations so a mis-set start date can never loop unbounded.
        for _iteration in range(500):
            if self.state != 'running' or not self.date_next \
                    or self.date_next > today:
                break
            if self.date_end and self.date_next > self.date_end:
                self.state = 'done'
                break
            moves |= self._create_invoice(self.date_next)
            next_date = self._next_date(self.date_next)
            self.date_next = next_date
            if self.date_end and next_date > self.date_end:
                self.state = 'done'
                break
        return moves

    def action_generate_now(self):
        """Manually generate the invoices currently due for this template."""
        self.ensure_one()
        if self.state == 'draft':
            self.action_start()
        moves = self._generate_due()
        if not moves:
            raise UserError(_("No invoice is due for '%s' yet.") % self.name)
        return self._action_view_moves(moves)

    @api.model
    def _cron_generate_invoices(self):
        """Scheduled generation for every running template that is due."""
        today = fields.Date.context_today(self)
        templates = self.search([
            ('state', '=', 'running'), ('date_next', '!=', False),
            ('date_next', '<=', today)])
        for template in templates:
            template._generate_due()

    def _action_view_moves(self, moves):
        action = {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        if len(moves) == 1:
            action.update(view_mode='form', res_id=moves.id)
        else:
            action.update(view_mode='list,form',
                          domain=[('id', 'in', moves.ids)])
        return action

    def action_view_invoices(self):
        self.ensure_one()
        return self._action_view_moves(self.invoice_ids)


class AccountRecurringInvoiceLine(models.Model):
    """A template line copied onto each generated invoice."""
    _name = 'account.recurring.invoice.line'
    _description = 'Recurring Invoice Line'

    recurring_id = fields.Many2one(
        'account.recurring.invoice', string='Recurring Invoice',
        required=True, ondelete='cascade')
    company_id = fields.Many2one(related='recurring_id.company_id')
    currency_id = fields.Many2one(related='recurring_id.currency_id')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    account_id = fields.Many2one(
        'account.account', string='Account',
        help="Leave empty to use the product/journal default account.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name
            if self.recurring_id.move_type == 'in_invoice':
                self.price_unit = self.product_id.standard_price
                self.tax_ids = self.product_id.supplier_taxes_id
            else:
                self.price_unit = self.product_id.lst_price
                self.tax_ids = self.product_id.taxes_id
