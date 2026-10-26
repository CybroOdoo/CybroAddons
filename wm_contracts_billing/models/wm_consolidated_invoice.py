#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WmConsolidatedInvoice(models.Model):
    """Groups multiple collection orders into one monthly customer invoice via a billing run."""
    _name = 'wm.consolidated.invoice'
    _description = 'Consolidated Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        tracking=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        tracking=True,
        default=lambda self: fields.Date.today().replace(day=1) + relativedelta(months=1, days=-1),
    )
    billing_month = fields.Char(
        string='Billing Month',
        compute='_compute_billing_month',
        store=True,
        help='YYYY-MM derived from date_from — used for duplicate prevention.',
    )
    order_ids = fields.Many2many(
        'wm.collection.order',
        'wm_consolidated_invoice_order_rel',
        'consolidated_invoice_id',
        'order_id',
        string='Collection Orders',
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('completed', 'signed')), ('consolidated_invoice_id', '=', False), ('billing_run_line_id', '=', False), ('direct_invoice_id', '=', False)]",
    )
    order_count = fields.Integer(
        string='Orders',
        compute='_compute_order_count',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False,
    )
    invoice_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment Status',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.depends('date_from')
    def _compute_billing_month(self):
        """
        Derive the billing month key (e.g. '2026-08') from the From Date, used
        to prevent duplicate invoices for the same month.
        """
        for rec in self:
            rec.billing_month = rec.date_from.strftime('%Y-%m') if rec.date_from else False

    @api.constrains('partner_id', 'billing_month', 'state')
    def _check_unique_monthly_invoice(self):
        """
        Prevent creation of more than one consolidated invoice per partner per
        billing month, ensuring duplicate invoice records are not generated
        during concurrent billing runs.
        """
        for rec in self:
            if rec.state == 'draft':
                continue  # Only enforce on invoiced records
            duplicate = self.search([
                ('partner_id', '=', rec.partner_id.id),
                ('company_id', '=', rec.company_id.id),
                ('billing_month', '=', rec.billing_month),
                ('state', '=', 'invoiced'),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "A monthly invoice already exists for %(partner)s "
                    "for %(month)s (%(ref)s). "
                    "Cancel it before generating a new one."
                ) % {
                    'partner': rec.partner_id.name,
                    'month': rec.date_from.strftime('%B %Y'),
                    'ref': duplicate.name,
                })

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """
        Validate that To Date is not earlier than From Date.
        """
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_("To Date cannot be earlier than From Date."))

    @api.depends('order_ids')
    def _compute_order_count(self):
        """
        Compute the total number of associated order records linked to this
        WmConsolidatedInvoice to update smart buttons and summary badges.
        """
        for rec in self:
            rec.order_count = len(rec.order_ids)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        When changing customer, remove collection orders that do not belong to
        the newly selected customer.
        """
        if self.partner_id:
            if self.order_ids:
                self.order_ids = self.order_ids.filtered(lambda o: o.partner_id == self.partner_id)
        else:
            self.order_ids = [(5, 0, 0)]

    @api.constrains('order_ids', 'partner_id')
    def _check_order_ids_partner(self):
        """
        Ensure all selected collection orders belong to the consolidated
        invoice's customer.
        """
        for rec in self:
            if rec.partner_id and rec.order_ids:
                mismatched = rec.order_ids.filtered(lambda o: o.partner_id != rec.partner_id)
                if mismatched:
                    names = ', '.join(mismatched.mapped('name'))
                    raise ValidationError(_(
                        "The following collection order(s) do not belong to customer '%(partner)s': %(orders)s"
                    ) % {
                        'partner': rec.partner_id.display_name,
                        'orders': names,
                    })

    @api.constrains('order_ids')
    def _check_order_ids_state(self):
        """
        Ensure only collection orders in 'completed' or 'signed' state are
        added to a consolidated invoice.
        """
        for rec in self:
            invalid_orders = rec.order_ids.filtered(
                lambda o: o.state not in ('completed', 'signed')
            )
            if invalid_orders:
                names = ', '.join(invalid_orders.mapped('name'))
                raise ValidationError(_(
                    "Only collection orders in 'Completed' or 'Signed' state can be added to a consolidated invoice.\n"
                    "The following order(s) are not in a billable state: %s"
                ) % names)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.consolidated.invoice') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        if 'partner_id' in vals and 'order_ids' not in vals:
            new_partner_id = vals['partner_id']
            for rec in self:
                if rec.partner_id.id != new_partner_id and rec.order_ids:
                    valid_order_ids = rec.order_ids.filtered(lambda o: o.partner_id.id == new_partner_id).ids
                    rec.order_ids = [(6, 0, valid_order_ids)]
        return super().write(vals)

    def action_generate_invoice(self):
        """
        Generate a single customer invoice covering all selected collection
        orders, aggregated by waste category.
        """
        self.ensure_one()
        if self.state == 'invoiced':
            raise UserError(_("This consolidated invoice has already been processed."))
        # Confirmed billable events in the period are invoiced even when the
        # customer had no collection orders.
        events = self.env['wm.billable.event'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'confirmed'),
            ('event_date', '>=', self.date_from),
            ('event_date', '<=', self.date_to),
        ])
        if not self.order_ids and not events:
            raise UserError(_("Please select at least one collection order to invoice."))

        already_billed = self.order_ids.filtered(
            lambda o: o.direct_invoice_id or o.billing_run_line_id
            or (o.consolidated_invoice_id and o.consolidated_invoice_id != self)
        )
        if already_billed:
            raise UserError(_(
                "Cannot generate invoice: the following orders are already billed: %s"
            ) % ', '.join(already_billed.mapped('name')))

        non_billable = self.order_ids.filtered(
            lambda o: o.state not in ('completed', 'signed')
        )
        if non_billable:
            raise UserError(_(
                "Cannot generate invoice: the following orders are not in a billable "
                "state (completed or signed): %s"
            ) % ', '.join(non_billable.mapped('name')))

        # Step 1: Aggregate weights per (contract, category) across ALL orders
        groups = self.order_ids._group_lines_for_billing()
        # Subscription allowance left for these orders, shared with the other
        # invoicing paths so it is never granted twice
        budget_of, remaining = self.order_ids._get_allowance_budgets()
        used = {}

        if self.order_ids and not groups:
            raise UserError(_(
                "No billable waste lines found across the selected orders. "
                "Ensure orders have waste category lines with weight > 0."
            ))

        invoice_lines = []
        contract_fees = {}

        # Section header — one for the whole period
        total_orders = len(self.order_ids)
        order_names = self.order_ids.mapped('name')
        if len(order_names) > 5:
            order_ref = ', '.join(order_names[:5]) + _(' (and %d more)') % (len(order_names) - 5)
        else:
            order_ref = ', '.join(order_names)

        invoice_lines.append((0, 0, {
            'display_type': 'line_section',
            'name': _(
                "%(period)s — %(count)d Collection(s) — %(partner)s"
            ) % {
                'period': self.date_from.strftime('%B %Y'),
                'count': total_orders,
                'partner': self.partner_id.name,
            },
        }))

        # Build one invoice line per category; contract per-collection fees
        # are collected and billed once per order after the loop. Every
        # collection is priced on its own weight (never pooled over the period),
        # exactly like the order total and the direct invoice. The allowance
        # goes to the highest price first.
        Order = self.env['wm.collection.order']
        company_lines = []  # priced in company currency, converted below
        for (contract, category), data in Order._sort_groups_for_allowance(groups, self.partner_id):
            rule = Order._get_billing_rule(
                category, partner=self.partner_id, date=data['date'], contract=contract
            )
            target = invoice_lines if (rule and getattr(rule, 'from_contract', False)) else company_lines
            order_weights = data['order_weights']
            cat_weight = data['weight']
            category_name = category.name
            service_product = getattr(category, 'service_product_id', False) or data['product']

            # A price per collection is not lowered by free kg: the
            # subscription allowance only applies to per-kg prices.
            if rule and getattr(rule, 'billing_basis', 'per_kg') in ('flat_per_collection', 'hybrid'):
                if getattr(rule, 'contract_id', 0):
                    fee = contract_fees.setdefault(rule.contract_id, {
                        'rule': rule, 'order_weights': {}, 'product': service_product,
                    })
                    for order_id, weight in order_weights.items():
                        fee['order_weights'][order_id] = fee['order_weights'].get(order_id, 0.0) + weight
                else:
                    target += Order._prepare_collection_fee_lines_per_order(
                        rule, order_weights, service_product, category_name)
                continue

            charged, credited = Order._split_allowance(order_weights, budget_of, remaining, used)
            fully_covered = not charged
            if fully_covered:
                # Every collection covered by the subscription: shown at its
                # weight and credited in full, no minimum
                charged, credited = order_weights, cat_weight
            cat_weight = sum(charged.values())

            if rule and fully_covered:
                price_per_kg = rule.price
                qty = cat_weight
                description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg") % {
                    'cat': category_name, 'wt': cat_weight, 'price': price_per_kg,
                }
            elif rule:
                price_per_kg = rule.price
                total, billed_weight, charge_applied = Order._price_per_kg_per_collection(
                    rule, list(charged.values()))
                if charge_applied:
                    qty = 1.0
                    price_per_kg = total
                    description = _("%(cat)s — %(wt).1f kg (minimum charge applied per collection)") % {
                        'cat': category_name, 'wt': cat_weight,
                    }
                else:
                    qty = billed_weight
                    description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg") % {
                        'cat': category_name, 'wt': billed_weight, 'price': price_per_kg,
                    }
            else:
                category_price = getattr(category, 'price', 0.0) or 0.0
                total_amount = data.get('amount', 0.0)
                if category_price > 0:
                    price_per_kg = category_price
                    qty = cat_weight
                    description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg [Category default rate]") % {
                        'cat': category_name, 'wt': cat_weight, 'price': category_price,
                    }
                elif total_amount and cat_weight:
                    avg_rate = total_amount / data['weight']
                    self.message_post(body=_(
                        "No pricing rule found for category '%(cat)s'. "
                        "Used average rate from order line prices (%(rate)s/kg)."
                    ) % {'cat': category_name, 'rate': round(avg_rate, 4)})
                    price_per_kg = avg_rate
                    qty = cat_weight
                    description = _("%(cat)s — %(wt).1f kg [Rate from order lines]") % {
                        'cat': category_name, 'wt': cat_weight,
                    }
                else:
                    # Never invoice (and mark orders as billed) at zero
                    raise UserError(_(
                        "No price could be resolved for category '%(cat)s' (%(wt).1f kg). "
                        "Configure a pricing rule or category price, then generate the invoice again."
                    ) % {'cat': category_name, 'wt': cat_weight})

            target.append((0, 0, {
                'product_id': service_product.id if service_product else False,
                'name': description,
                'quantity': qty,
                'price_unit': price_per_kg,
            }))
            if credited:
                rate = rule.price if rule else price_per_kg
                target.append(Order._prepare_allowance_discount_line(
                    category_name, credited, rate, service_product))

        for contract_id, fee in contract_fees.items():
            invoice_lines += Order._prepare_collection_fee_lines_per_order(
                fee['rule'], fee['order_weights'], fee['product'],
                self.env['wm.partner.contract'].browse(contract_id).display_name)

        # Invoice in the currency of the orders' contracts (company currency
        # without a contract); prices that do not come from a contract are in
        # the company currency and are converted.
        currencies = {
            (order.contract_id.currency_id or self.company_id.currency_id) for order in self.order_ids
        }
        if len(currencies) > 1:
            raise UserError(_(
                "The selected orders belong to contracts in different currencies (%s). "
                "Invoice them separately."
            ) % ', '.join(sorted(c.name for c in currencies)))
        invoice_currency = currencies.pop() if currencies else self.company_id.currency_id
        invoice_lines += Order._scale_invoice_lines(
            company_lines,
            Order._get_invoice_currency_factor(invoice_currency, self.company_id, self.date_to))

        if events:
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _("Ad-Hoc / Service Events"),
            }))
            for event in events:
                event_label = dict(event._fields['event_type'].selection).get(event.event_type, event.event_type)
                invoice_lines.append((0, 0, {
                    'name': _("%(type)s — %(date)s (Ref: %(ref)s)") % {
                        'type': event_label,
                        'date': event.event_date.strftime('%d/%m/%Y'),
                        'ref': event.name,
                    },
                    'quantity': event.quantity or 1.0,
                    'price_unit': (event.currency_id or invoice_currency)._convert(
                        event.price_unit, invoice_currency, self.company_id,
                        event.event_date or fields.Date.today()),
                    'discount': min(max(event.discount_pct or 0.0, 0.0), 100.0),
                }))

        # Note line: source order references
        invoice_lines.append((0, 0, {
            'display_type': 'line_note',
            'name': _(
                "Period: %(from)s – %(to)s  ·  Source orders: %(orders)s"
            ) % {
                'from': self.date_from.strftime('%d/%m/%Y'),
                'to': self.date_to.strftime('%d/%m/%Y'),
                'orders': order_ref,
            },
        }))

        # Create the invoice
        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': invoice_currency.id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today() + relativedelta(days=30),
            'ref': self.name,
            'invoice_line_ids': invoice_lines,
        })

        # Link invoice to consolidated record, mark events as invoiced and orders as billed
        self.invoice_id = invoice.id
        self.order_ids.sudo().write({'consolidated_invoice_id': self.id})
        self.order_ids._record_allowance_usage(budget_of, used)
        if events:
            events.sudo().write({'state': 'invoiced', 'invoice_id': invoice.id})
        self.write({'state': 'invoiced'})

        self.message_post(body=Markup(_(
            "Monthly invoice <b>%s</b> generated covering %d orders "
            "(%s to %s)."
        )) % (escape(invoice.name or ''), total_orders,
             self.date_from.strftime('%d/%m/%Y'), self.date_to.strftime('%d/%m/%Y')))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoice(self):
        """
        Open the account.move customer invoice record linked to this
        consolidated invoice for viewing, printing, or payment reconciliation.
        """
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No invoice has been generated yet."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_orders(self):
        """
        Display all collection orders bundled into this consolidated invoice,
        enabling customer service to verify which services were included in the
        billing period.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Collection Orders'),
            'res_model': 'wm.collection.order',
            'view_mode': 'list,form',
            'domain': [('consolidated_invoice_id', '=', self.id)],
        }

    def action_reset_to_draft(self):
        """
        Reset to draft (only allowed if invoice is not yet posted/paid).
        """
        for rec in self:
            if rec.invoice_id and rec.invoice_id.state != 'cancel':
                raise UserError(_(
                    "Cannot reset to draft: the linked invoice (%s) is not cancelled. "
                    "Please cancel the invoice first."
                ) % rec.invoice_id.name)
            # Unlink orders from consolidated invoice
            rec.order_ids.sudo().write({'consolidated_invoice_id': False})
            # Release the billable events of the cancelled invoice so they are
            # picked up again by the next consolidated invoice.
            if rec.invoice_id:
                self.env['wm.billable.event'].sudo().search([
                    ('invoice_id', '=', rec.invoice_id.id),
                    ('state', '=', 'invoiced'),
                ]).write({'state': 'confirmed', 'invoice_id': False, 'invoice_line_id': False})
            # Note: do NOT change order state — they remain completed/signed
            rec.write({'state': 'draft', 'invoice_id': False})

    @api.ondelete(at_uninstall=False)
    def _unlink_except_invoiced(self):
        """
        Block deleting an invoiced record: unlinking would free its orders
        (consolidated_invoice_id is set null) and let them be billed again.
        """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    "Consolidated invoice %s is invoiced and cannot be deleted. "
                    "Cancel its invoice and reset it to draft first."
                ) % rec.name)

    @api.model
    def _cron_generate_monthly_invoices(self):
        """
        Runs on the 1st of each month (configured in ir.cron).
        Auto-generates monthly invoices for all customers with unbilled
        completed/signed orders in the previous month.
        """
        today = fields.Date.today()
        date_from = (today.replace(day=1) - relativedelta(months=1))
        date_to = today.replace(day=1) - timedelta(days=1)

        generated = 0
        errors = []

        # Bill each company separately, with only that company's orders and events
        for company in self.env['res.company'].sudo().search([]):
            invoice_model = self.sudo().with_company(company)
            partners = invoice_model.env['res.partner'].search([
                ('billing_mode', '=', 'consolidated'),
                ('company_id', 'in', (False, company.id)),
            ])
            for partner in partners:
                partner_orders = invoice_model.env['wm.collection.order']._get_billable_orders(
                    partner, date_from, date_to).filtered(lambda o: o.company_id == company)
                partner_events = invoice_model.env['wm.billable.event'].search([
                    ('partner_id', '=', partner.id),
                    ('company_id', '=', company.id),
                    ('state', '=', 'confirmed'),
                    ('event_date', '>=', date_from),
                    ('event_date', '<=', date_to),
                ])
                if not partner_orders and not partner_events:
                    continue
                try:
                    # Roll back this partner's record and invoice on failure, so no
                    # orphan account.move or half-linked orders get committed.
                    with self.env.cr.savepoint():
                        consolidated = invoice_model.create({
                            'partner_id': partner.id,
                            'company_id': company.id,
                            'date_from': date_from,
                            'date_to': date_to,
                            'order_ids': [fields.Command.set(partner_orders.ids)],
                        })
                        consolidated.action_generate_invoice()
                    generated += 1
                except Exception as e:
                    _logger.error("Failed to generate consolidated invoice for partner %s: %s", partner.name, e, exc_info=True)
                    errors.append(f"{partner.name}: {e}")

        if errors:
            _logger.error("Monthly billing cron completed with errors:\n%s", '\n'.join(errors))
        _logger.info("Monthly billing cron: %d invoices generated.", generated)
