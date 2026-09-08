# -*- coding: utf-8 -*-
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
from markupsafe import escape, Markup
from odoo import api, fields, models, _
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
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('completed', 'signed')), ('consolidated_invoice_id', '=', False), ('billing_run_line_id', '=', False)]",
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
        Derive the billing month label (e.g. 'August 2026') from the billing
        run's period_start date for display on the consolidated invoice header.
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

    def _find_pricing_rule(self, category, date):
        """
        Find the best-matching wm.pricing.rule for a category on a given date.
        Priority: customer-specific rule first, then general (no partner) rule.
        Returns the rule record or False.
        """
        PricingRule = self.env['wm.pricing.rule']
        base_domain = [
            ('waste_category_id', '=', category.id),
            ('active', '=', True),
            ('effective_date', '<=', date),
            '|', ('expiry_date', '=', False), ('expiry_date', '>=', date),
        ]
        # Customer-specific rule (higher priority)
        partner_rule = PricingRule.search(
            base_domain + [('partner_id', '=', self.partner_id.id)],
            limit=1, order='sequence asc'
        )
        if partner_rule:
            return partner_rule
        # General rule (all customers)
        return PricingRule.search(
            base_domain + [('partner_id', '=', False)],
            limit=1, order='sequence asc'
        )

    def _resolve_category_price(self, category, data, contract, today):
        """
        Resolve price_per_kg, quantity, and description for a category
        aggregate.         Returns: (price_per_kg: float, quantity: float,
        description: str)          Priority chain:           1. Contract
        category_rate line (if contract has billing_basis='category_rate')
        2. Contract per_collection or hybrid (flat fee handled separately — not
        per category)           3. Customer-specific wm.pricing.rule
        4. General wm.pricing.rule           5. category.price (flat field on
        wm.waste.category)           6. Computed average from collected order
        line amounts (fallback — warns)
        """
        weight = data['weight']
        category_name = category.name

        rule = self.env['wm.collection.order']._get_billing_rule(category, self.partner_id, today)
        if rule:
            price = getattr(rule, 'price', getattr(rule, 'price_per_kg', 0.0))
            min_weight = getattr(rule, 'min_weight', 0.0) or 0.0
            min_charge = getattr(rule, 'min_charge', 0.0) or 0.0

            weight_to_bill = max(weight, min_weight) if min_weight else weight
            line_total = weight_to_bill * price
            if min_charge and line_total < min_charge:
                line_total = min_charge

            quantity = weight_to_bill if weight_to_bill > 0 else 1.0
            price_unit = line_total / quantity
            return (
                price_unit,
                quantity,
                _("%(cat)s — %(wt).1f kg @ %(price)s/kg") % {
                    'cat': category_name, 'wt': weight, 'price': round(price_unit, 2),
                }
            )

        # Fallback 1: category.price (flat field on wm.waste.category)
        category_price = getattr(category, 'price', 0.0) or 0.0
        if category_price > 0:
            return (
                category_price,
                weight,
                _("%(cat)s — %(wt).1f kg @ %(price)s/kg [Category default rate]") % {
                    'cat': category_name, 'wt': weight, 'price': category_price,
                }
            )

        # Fallback 2: zero with warning
        self.message_post(body=_(
            "⚠ No price resolved for category '%(cat)s' (%(wt).1f kg). "
            "Invoice line created with price = 0. "
            "Configure a billing rule to fix this."
        ) % {'cat': category_name, 'wt': weight})
        return (0.0, weight, _("%(cat)s — %(wt).1f kg [NO PRICE]") % {
            'cat': category_name, 'wt': weight,
        })

    def action_generate_invoice(self):
        """
        Generate a single customer invoice covering all selected collection
        orders,         aggregated by waste category.
        """
        self.ensure_one()
        if self.state == 'invoiced':
            raise UserError(_("This consolidated invoice has already been processed."))
        if not self.order_ids:
            raise UserError(_("Please select at least one collection order to invoice."))

        non_billable = self.order_ids.filtered(
            lambda o: o.state not in ('completed', 'signed')
        )
        if non_billable:
            raise UserError(_(
                "Cannot generate invoice: the following orders are not in a billable "
                "state (completed or signed): %s"
            ) % ', '.join(non_billable.mapped('name')))

        # Step 1: Aggregate weights by category across ALL orders
        category_totals = {}

        for order in self.order_ids:
            for line in order.order_line_ids:
                category = getattr(line, 'category_id', False)
                if not category and line.product_id:
                    category = getattr(line.product_id, 'wm_waste_category_id', False)
                if not category:
                    continue
                if category not in category_totals:
                    category_totals[category] = {
                        'weight': 0.0,
                        'amount': 0.0,
                        'product': line.product_id,
                        'orders': set(),
                    }
                category_totals[category]['weight'] += line.weight
                category_totals[category]['amount'] += line.total_amount
                category_totals[category]['orders'].add(order.id)

        if not category_totals:
            raise UserError(_(
                "No billable waste lines found across the selected orders. "
                "Ensure orders have waste category lines with weight > 0."
            ))

        # Step 2: Find active contract for partner
        self.env['wm.partner.contract'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'ongoing'),
        ], limit=1)

        today = fields.Date.today()
        invoice_lines = []

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

        # Build one invoice line per category
        for category, data in category_totals.items():
            rule = self.env['wm.collection.order']._get_billing_rule(
                category, partner=self.partner_id, date=today
            )
            cat_weight = data['weight']
            category_name = category.name

            if rule:
                billing_basis = getattr(rule, 'billing_basis', 'per_kg')
                if billing_basis == 'flat_per_collection':
                    order_count = len(data['orders'])
                    flat_total = rule.price * order_count
                    max_weight = getattr(rule, 'max_weight', 0.0) or 0.0
                    overweight_price = getattr(rule, 'overweight_price', 0.0) or 0.0
                    allowed_weight = max_weight * order_count
                    overweight_surcharge = 0.0
                    if allowed_weight and overweight_price and cat_weight > allowed_weight:
                        overweight_kg = cat_weight - allowed_weight
                        overweight_surcharge = (overweight_kg / 10.0) * overweight_price
                    price_per_kg = flat_total + overweight_surcharge
                    qty = 1.0
                    description = _("%(cat)s — %(count)d collection(s) @ %(price)s/collection") % {
                        'cat': category_name, 'count': order_count, 'price': rule.price,
                    }
                    if overweight_surcharge:
                        description += _(" + overweight surcharge %(surcharge)s") % {
                            'surcharge': round(overweight_surcharge, 2)
                        }
                elif billing_basis == 'hybrid':
                    order_count = len(data['orders'])
                    base_total = rule.price * order_count
                    included_weight = getattr(rule, 'included_weight', 0.0) or getattr(rule, 'min_weight', 0.0) or 0.0
                    overweight_price = getattr(rule, 'overweight_price', 0.0) or getattr(rule, 'min_charge', 0.0) or 0.0
                    allowed_weight = included_weight * order_count
                    overweight_surcharge = 0.0
                    if allowed_weight and overweight_price and cat_weight > allowed_weight:
                        overage_kg = cat_weight - allowed_weight
                        overweight_surcharge = (overage_kg / 10.0) * overweight_price
                    price_per_kg = base_total + overweight_surcharge
                    qty = 1.0
                    description = _(
                        "%(cat)s — %(count)d collection(s), %(wt).1f kg "
                        "(base: %(base)s, overage: %(surcharge)s)"
                    ) % {
                        'cat': category_name, 'count': order_count, 'wt': cat_weight,
                        'base': round(base_total, 2), 'surcharge': round(overweight_surcharge, 2),
                    }
                else:
                    price_per_kg = rule.price
                    min_wt = getattr(rule, 'min_weight', 0.0) or 0.0
                    qty = max(cat_weight, min_wt) if min_wt else cat_weight
                    description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg") % {
                        'cat': category_name, 'wt': qty, 'price': price_per_kg,
                    }
            else:
                category_price = getattr(category, 'price', 0.0) or 0.0
                if category_price > 0:
                    price_per_kg = category_price
                    qty = cat_weight
                    description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg [Category default rate]") % {
                        'cat': category_name, 'wt': cat_weight, 'price': category_price,
                    }
                else:
                    total_amount = data.get('amount', 0.0)
                    if total_amount and cat_weight:
                        avg_rate = total_amount / cat_weight
                        self.message_post(body=_(
                            "⚠ No pricing rule found for category '%(cat)s'. "
                            "Used average rate from order line prices (%(rate)s/kg)."
                        ) % {'cat': category_name, 'rate': round(avg_rate, 4)})
                        price_per_kg = avg_rate
                        qty = cat_weight
                        description = _("%(cat)s — %(wt).1f kg [Rate from order lines]") % {
                            'cat': category_name, 'wt': cat_weight,
                        }
                    else:
                        price_per_kg = 0.0
                        qty = cat_weight
                        self.message_post(body=_(
                            "⚠ No price resolved for category '%(cat)s' (%(wt).1f kg). "
                            "Invoice line created with price = 0. "
                            "Configure a billing rule to fix this."
                        ) % {'cat': category_name, 'wt': cat_weight})
                        description = _("%(cat)s — %(wt).1f kg [NO PRICE — configure pricing rule]") % {
                            'cat': category_name, 'wt': cat_weight,
                        }

            service_product = getattr(category, 'service_product_id', False)
            if not service_product:
                service_product = data['product']

            # Apply minimum charge for per_kg basis rules
            if rule and getattr(rule, 'billing_basis', 'per_kg') == 'per_kg':
                raw_amount = price_per_kg * qty
                min_charge = getattr(rule, 'min_charge', 0.0) if rule else 0.0

                if min_charge and raw_amount < min_charge:
                    qty = 1.0
                    price_per_kg = min_charge
                    description += _(" (minimum charge applied)")

            invoice_lines.append((0, 0, {
                'product_id': service_product.id if service_product else False,
                'name': description,
                'quantity': qty,
                'price_unit': price_per_kg,
                'tax_ids': [(5, 0, 0)],
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
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today() + relativedelta(days=30),
            'ref': self.name,
            'invoice_line_ids': invoice_lines,
        })

        # Link invoice to consolidated record and mark orders as billed
        self.invoice_id = invoice.id
        self.order_ids.sudo().write({'consolidated_invoice_id': self.id})
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
            # Note: do NOT change order state — they remain completed/signed
            rec.write({'state': 'draft', 'invoice_id': False})

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

        partners = self.env['res.partner'].search([('billing_mode', '=', 'consolidated')])
        generated = 0
        errors = []

        for partner in partners:
            partner_orders = self.env['wm.collection.order']._get_billable_orders(partner, date_from, date_to)
            if not partner_orders:
                continue
            try:
                consolidated = self.create({
                    'partner_id': partner.id,
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
