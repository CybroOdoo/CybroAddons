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
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class WmCollectionOrder(models.Model):
    """Extends Collection Order with contract determination and consolidated billing fields."""
    _inherit = 'wm.collection.order'

    # Contract Fields
    contract_id = fields.Many2one(
        'wm.partner.contract', string='Contract',
        compute='_compute_contract_id', store=True, precompute=True, ondelete='set null'
    )
    contract_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_contract_product_ids',
        string='Contract Waste Materials',
        help='Waste materials allowed by the contract. If empty, any waste material can be selected.'
    )

    # Billing Fields
    consolidated_invoice_id = fields.Many2one(
        'wm.consolidated.invoice',
        string='Consolidated Invoice',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="The consolidated invoice that covers this collection order's charges.",
    )
    billing_run_line_id = fields.Many2one(
        'wm.monthly.billing.run.line',
        string='Monthly Billing Run Line',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="The monthly billing run line that includes this collection order.",
    )
    direct_invoice_id = fields.Many2one(
        'account.move',
        string='Direct Invoice',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="Customer invoice created manually from this collection order form.",
    )
    invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_invoice_ids',
        string='Invoices',
        help='Invoices generated for this collection order via direct action, consolidated billing, or monthly run.'
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count',
        help='Number of invoices linked to this collection order.'
    )

    portal_request_id = fields.Many2one(
        'wm.portal.service.request',
        string='Portal Service Request',
        readonly=True,
        ondelete='set null',
        copy=False,
        help='Customer portal service request that generated this collection order.'
    )
    is_consolidated = fields.Boolean(
        string='Consolidated',
        compute='_compute_is_consolidated',
        store=True,
        help="True when this order has been included in a consolidated invoice.",
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)

    @api.depends('consolidated_invoice_id', 'consolidated_invoice_id.invoice_id', 'billing_run_line_id', 'billing_run_line_id.invoice_id', 'direct_invoice_id')
    def _compute_invoice_ids(self):
        """
        Compute invoices linked to this collection order through direct invoicing,
        consolidated invoice, or monthly billing run. For a billing run only
        the order's own run line invoice counts: the run's invoices belong to
        every billed customer (a run line without an invoice, e.g. covered by
        the subscription allowance, has none).
        """
        for order in self:
            invoices = self.env['account.move']
            if order.direct_invoice_id:
                invoices |= order.direct_invoice_id
            if order.consolidated_invoice_id and order.consolidated_invoice_id.invoice_id:
                invoices |= order.consolidated_invoice_id.invoice_id
            if order.billing_run_line_id.invoice_id:
                invoices |= order.billing_run_line_id.invoice_id
            order.invoice_ids = invoices

    def action_view_invoices(self):
        """Open invoices linked to this collection order."""
        self.ensure_one()
        invoices = self.invoice_ids
        action = {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False},
        }
        if len(invoices) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = invoices.id
        return action

    @api.depends('partner_id', 'collection_point_id')
    def _compute_contract_id(self):
        """
        Compute the active ongoing contract for the customer/collection point.
        """
        for order in self:
            if order.state != 'draft':
                order.contract_id = order._origin.contract_id
                continue

            if order.contract_id:
                contract = order.contract_id
                if order.partner_id and contract.partner_id == order.partner_id and contract.state == 'ongoing':
                    continue

            if order.partner_id:
                domain = [
                    ('partner_id', '=', order.partner_id.id),
                    ('state', '=', 'ongoing'),
                ]
                if order.collection_point_id:
                    domain.append(('collection_point_ids', 'in', order.collection_point_id.id))

                ongoing_contract = self.env['wm.partner.contract'].search(domain, limit=1)

                if not ongoing_contract and order.collection_point_id:
                    ongoing_contract = self.env['wm.partner.contract'].search([
                        ('partner_id', '=', order.partner_id.id),
                        ('state', '=', 'ongoing'),
                    ], limit=1)

                order.contract_id = ongoing_contract.id if ongoing_contract else False
            else:
                order.contract_id = False

    @api.depends(
        'contract_id',
        'contract_id.contract_line_ids',
        'contract_id.contract_line_ids.product_ids',
        'contract_id.contract_line_ids.category_id'
    )
    def _compute_contract_product_ids(self):
        """
        Compute waste material products specified in the active contract.
        """
        for order in self:
            if order.contract_id and order.contract_id.contract_line_ids:
                allowed_products = self.env['product.product']
                for line in order.contract_id.contract_line_ids:
                    if line.product_ids:
                        allowed_products |= line.product_ids
                    elif line.category_id:
                        cat_products = self.env['product.product'].search([
                            ('is_waste_material', '=', True),
                            ('wm_waste_category_id', '=', line.category_id.id),
                        ])
                        allowed_products |= cat_products
                order.contract_product_ids = allowed_products
            else:
                order.contract_product_ids = False

    @api.depends('contract_id', 'contract_id.contract_line_ids.category_id', 'collection_point_id', 'collection_point_id.category_ids')
    def _compute_collection_point_category_ids(self):
        """
        Derive the list of waste categories serviced at the collection point,
        used to filter and default the contract line category selection in the
        billing form.
        """
        super()._compute_collection_point_category_ids()
        for order in self:
            if order.contract_id and order.contract_id.contract_line_ids:
                order.collection_point_category_ids = order.contract_id.contract_line_ids.category_id

    @api.depends('consolidated_invoice_id', 'billing_run_line_id')
    def _compute_is_consolidated(self):
        """
        Determine whether this collection order has been included in a
        consolidated invoice run, preventing duplicate billing and showing a
        consolidated invoice badge.
        """
        for order in self:
            order.is_consolidated = bool(order.consolidated_invoice_id or order.billing_run_line_id)

    @api.depends('consolidated_invoice_id', 'billing_run_line_id', 'direct_invoice_id')
    def _compute_is_billed(self):
        """
        Flag the collection order as billed once a linked invoice or billing
        run line reaches a confirmed/posted state, locking further billing
        actions on this order.
        """
        for order in self:
            order.is_billed = bool(order.consolidated_invoice_id or order.billing_run_line_id or order.direct_invoice_id)

    @api.constrains('consolidated_invoice_id', 'billing_run_line_id', 'direct_invoice_id')
    def _check_single_billing_pipeline(self):
        """
        An order can be billed through only one pipeline: consolidated
        invoice, monthly billing run or direct invoice.
        """
        for order in self:
            pipelines = [order.consolidated_invoice_id, order.billing_run_line_id, order.direct_invoice_id]
            if len([p for p in pipelines if p]) > 1:
                raise ValidationError(_(
                    "Collection Order %s is already billed and cannot be claimed by "
                    "another billing pipeline (consolidated invoice, monthly billing "
                    "run or direct invoice)."
                ) % order.name)

    _check_single_billing_pipeline_constraint = models.Constraint(
        'CHECK(NOT (consolidated_invoice_id IS NOT NULL AND billing_run_line_id IS NOT NULL))',
        'A collection order cannot be billed by both consolidated invoice and monthly billing run.'
    )

    def _group_lines_for_billing(self):
        """
        Aggregate the waste lines of these orders per (contract, category).

        :return: dict {(contract, category): {'weight', 'amount', 'product',
            'orders' (set of order ids), 'date' (latest service date)}}
        """
        groups = {}
        for order in self:
            service_date = order._get_billing_service_date()
            for line in order.order_line_ids:
                category = getattr(line, 'category_id', False) or (
                    getattr(line.product_id, 'wm_waste_category_id', False) if line.product_id else False
                )
                if not category:
                    continue
                data = groups.setdefault((order.contract_id, category), {
                    'weight': 0.0,
                    'amount': 0.0,
                    'product': line.product_id,
                    'orders': set(),
                    'order_weights': {},
                    'date': service_date,
                })
                data['weight'] += line.weight
                data['amount'] += line.total_amount
                data['orders'].add(order.id)
                data['order_weights'][order.id] = data['order_weights'].get(order.id, 0.0) + line.weight
                data['date'] = max(data['date'], service_date)
        return groups

    def _get_allowance_budgets(self):
        """
        Hook (wm_subscription): the subscription allowance these orders can
        use. Every invoicing path (monthly run, consolidated and direct
        invoice) takes its free weight from here, so an allowance is never
        granted twice.

        :return: ({order id: allowance key}, {allowance key: kg left})
        """
        return {}, {}

    def _record_allowance_usage(self, budget_of, used):
        """
        Hook (wm_subscription): remember the allowance each of these orders
        used once they are billed.

        :param used: {order id: kg covered by the allowance}
        """

    @api.model
    def _take_allowance(self, order_weights, budget_of, remaining, used):
        """
        Take the subscription allowance off each collection's weight, order
        by order, consuming ``remaining`` and adding to ``used`` in place.

        :param order_weights: {order id: weight kg}
        :return: {order id: weight kg still to bill}
        """
        billable = {}
        for order_id in sorted(order_weights):
            weight = order_weights[order_id]
            key = budget_of.get(order_id)
            if key and remaining.get(key, 0.0) > 0 and weight > 0:
                offset = min(remaining[key], weight)
                remaining[key] -= offset
                used[order_id] = used.get(order_id, 0.0) + offset
                weight -= offset
            billable[order_id] = weight
        return billable

    @api.model
    def _sort_groups_for_allowance(self, groups, partner):
        """
        Billing groups (see ``_group_lines_for_billing``), highest price
        first, so the free allowance is applied where it saves the most,
        deterministically.
        """
        def _priority(item):
            (contract, category), data = item
            rule = self._get_billing_rule(category, partner, data['date'], contract=contract)
            price = (rule.price if rule else category.price) or 0.0
            return (-price, category.id, contract.id if contract else 0)
        return sorted(groups.items(), key=_priority)

    @api.model
    def _split_allowance(self, order_weights, budget_of, remaining, used):
        """
        Apply the subscription allowance to collections priced per kg. A
        collection it covers completely is free (no minimum either). The
        others are still priced on their full weight, minimums included, and
        the kg covered on them are credited at the line's rate (see
        ``_prepare_allowance_discount_line``), so the allowance always lowers
        the bill instead of disappearing under a minimum weight.

        :param order_weights: {order id: weight kg}
        :return: ({order id: weight kg} of the collections still charged,
                  kg to credit on them)
        """
        left = self._take_allowance(order_weights, budget_of, remaining, used)
        charged = {order_id: weight for order_id, weight in order_weights.items()
                   if not (weight > 0 and left[order_id] <= 0)}
        credited = sum(weight - left[order_id] for order_id, weight in charged.items())
        return charged, credited

    @api.model
    def _prepare_allowance_discount_line(self, label, kg, rate, product=False):
        """Negative invoice line crediting the kg covered by the subscription allowance."""
        return (0, 0, {
            'product_id': product.id if product else False,
            'name': _("Subscription allowance — %(label)s: %(kg).1f kg @ %(rate)s/kg") % {
                'label': label, 'kg': kg, 'rate': rate,
            },
            'quantity': kg,
            'price_unit': -rate,
        })

    @api.model
    def _prepare_collection_fee_lines_per_order(self, rule, order_weights, product, label):
        """
        Invoice lines of a flat_per_collection or hybrid rule for several
        collections, each priced on its own weight (never pooled): the base fee
        per collection, plus one line summing the overweight surcharge of the
        collections that exceeded their allowance.

        :param order_weights: {order id: weight kg}
        """
        count = len(order_weights)
        surcharge = overweight_kg = 0.0
        for weight in order_weights.values():
            _base, order_surcharge, order_over_kg, _allowed = self._compute_collection_fee(rule, weight, 1)
            surcharge += order_surcharge
            overweight_kg += order_over_kg
        product_id = product.id if product else False
        lines = [(0, 0, {
            'product_id': product_id,
            'name': _("%(label)s — %(count)d collection(s) @ %(price)s/collection") % {
                'label': label, 'count': count, 'price': rule.price,
            },
            'quantity': count,
            'price_unit': rule.price,
        })]
        if surcharge:
            lines.append((0, 0, {
                'product_id': product_id,
                'name': _("%(label)s — overweight surcharge: %(kg).1f kg above the per-collection allowance") % {
                    'label': label, 'kg': overweight_kg,
                },
                'quantity': 1.0,
                'price_unit': surcharge,
            }))
        return lines

    @api.model
    def _price_per_kg_per_collection(self, rule, order_weights):
        """
        Amount of a per-kg rule for several collections, applying the rule's
        minimum weight and minimum charge to each collection on its own.

        :param order_weights: iterable of weights (kg), one per collection
        :return: (total amount, billed weight after the minimum weight,
                  True when the minimum charge raised the amount of a collection)
        """
        min_wt = getattr(rule, 'min_weight', 0.0) or 0.0
        min_charge = getattr(rule, 'min_charge', 0.0) or 0.0
        total = billed_weight = 0.0
        charge_applied = False
        for weight in order_weights:
            billed = max(weight, min_wt) if min_wt else weight
            amount = billed * rule.price
            if min_charge and amount < min_charge:
                amount = min_charge
                charge_applied = True
            total += amount
            billed_weight += billed
        return total, billed_weight, charge_applied

    @api.model
    def _get_invoice_currency_factor(self, currency, company, date):
        """Rate to convert a company-currency price into the invoice currency."""
        company_currency = company.currency_id
        if not currency or currency == company_currency:
            return 1.0
        return company_currency._convert(1.0, currency, company, date or fields.Date.today())

    @api.model
    def _scale_invoice_lines(self, lines, factor):
        """Multiply the unit price of prepared (0, 0, vals) invoice lines."""
        if factor == 1.0:
            return lines
        scaled = []
        for cmd in lines:
            vals = dict(cmd[2])
            if 'price_unit' in vals:
                vals['price_unit'] = vals['price_unit'] * factor
            scaled.append((0, 0, vals))
        return scaled

    @api.model
    def _prepare_collection_fee_lines(self, rule, weight, order_count, product, label):
        """
        Invoice line values for a flat_per_collection or hybrid rule: the base
        fee per collection, plus an overweight surcharge (per 10 kg) above the
        weight allowed for those collections.
        """
        _base, surcharge, overweight_kg, allowed_weight = self._compute_collection_fee(rule, weight, order_count)
        product_id = product.id if product else False
        lines = [(0, 0, {
            'product_id': product_id,
            'name': _("%(label)s — %(count)d collection(s) @ %(price)s/collection") % {
                'label': label, 'count': order_count, 'price': rule.price,
            },
            'quantity': order_count,
            'price_unit': rule.price,
        })]
        if surcharge:
            lines.append((0, 0, {
                'product_id': product_id,
                'name': _("%(label)s — overweight surcharge: %(kg).1f kg above %(allowed).1f kg allowance") % {
                    'label': label, 'kg': overweight_kg, 'allowed': allowed_weight,
                },
                'quantity': 1.0,
                'price_unit': surcharge,
            }))
        return lines

    def _prepare_direct_invoice_lines(self, company_price_factor=1.0, allowance=None):
        """
        Invoice line values for the direct invoice of this order, built from
        the order lines the same way the order total is computed, so manual
        price overrides on the lines are what gets invoiced:

        - per_kg lines: line price x weight, grouped per category, product
          and price;
        - per_collection lines: their flat price, once per line;
        - contract_fee lines: the contract's per-collection fee (and
          overweight surcharge) once for the order, via the shared
          ``_compute_collection_fee`` / ``_prepare_collection_fee_lines``.

        Minimums: a rate rule's minimum weight / minimum charge is still
        applied to a per-kg group billed at the rule's own rate (the rate
        card minimum, applied by the consolidated invoice and the monthly run
        too). It is not applied when the line price was overridden manually:
        the price entered on the order is then the agreed amount. Without a
        minimum the invoice untaxed amount equals the order total.

        ``company_price_factor`` converts prices that do not come from the
        contract (rate cards, pricing rules, defaults: company currency) into
        the invoice currency when it is the contract's currency.

        ``allowance`` is ``(budget_of, remaining, used)`` from
        ``_get_allowance_budgets``: the subscription allowance goes to the
        highest per-kg price first and is credited on its own line (see
        ``_split_allowance``); ``used`` is filled in.
        """
        self.ensure_one()
        budget_of, remaining, used = allowance or ({}, {}, {})
        invoice_lines = []
        per_kg = {}
        fee_lines = self.env['wm.collection.order.line']
        fee_product = False
        for line in self.order_line_ids:
            category = line.category_id or (line.product_id.wm_waste_category_id if line.product_id else False)
            if not category:
                continue
            service_product = getattr(category, 'service_product_id', False) or line.product_id
            if line.price_basis == 'contract_fee':
                fee_lines |= line
                fee_product = fee_product or service_product
            elif line.price_basis == 'per_collection':
                line_rule = line._get_billing_rule()
                factor = 1.0 if (line_rule and getattr(line_rule, 'from_contract', False)) else company_price_factor
                invoice_lines.append((0, 0, {
                    'product_id': service_product.id if service_product else False,
                    'name': _("%(cat)s — 1 collection @ %(price)s/collection") % {
                        'cat': category.name, 'price': line.price,
                    },
                    'quantity': 1.0,
                    'price_unit': line.price * factor,
                }))
            else:
                # Same weight as the order total (estimated until weighed)
                data = per_kg.setdefault((category, service_product, line.price), {
                    'weight': 0.0, 'line': line,
                })
                data['weight'] += line.weight or line.estimated_weight or 0.0

        currency = self.company_id.currency_id or self.env.company.currency_id
        for (category, service_product, price), data in sorted(per_kg.items(), key=lambda item: -item[0][2]):
            rule = data['line']._get_billing_rule()
            factor = 1.0 if (rule and getattr(rule, 'from_contract', False)) else company_price_factor
            charged, credited = self._split_allowance({self.id: data['weight']}, budget_of, remaining, used)
            qty = data['weight']
            price_unit = price
            description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg") % {
                'cat': category.name, 'wt': qty, 'price': price,
            }
            if not charged:
                # Fully covered by the subscription: shown at its weight and
                # credited in full, no minimum
                invoice_lines += [
                    (0, 0, {
                        'product_id': service_product.id if service_product else False,
                        'name': description,
                        'quantity': qty,
                        'price_unit': price * factor,
                    }),
                    self._prepare_allowance_discount_line(category.name, qty, price * factor, service_product),
                ]
                continue
            rule_price = getattr(rule, 'price', getattr(rule, 'price_per_kg', 0.0)) if rule else 0.0
            if (rule and getattr(rule, 'billing_basis', 'per_kg') == 'per_kg'
                    and not currency.compare_amounts(price, rule_price or 0.0)):
                min_wt = getattr(rule, 'min_weight', 0.0) or 0.0
                if min_wt and qty < min_wt:
                    qty = min_wt
                    description = _("%(cat)s — %(wt).1f kg @ %(price)s/kg (minimum weight applied)") % {
                        'cat': category.name, 'wt': qty, 'price': price,
                    }
                min_charge = getattr(rule, 'min_charge', 0.0) or 0.0
                if min_charge and currency.compare_amounts(price * qty, min_charge) < 0:
                    qty = 1.0
                    price_unit = min_charge
                    description += _(" (minimum charge applied)")
            invoice_lines.append((0, 0, {
                'product_id': service_product.id if service_product else False,
                'name': description,
                'quantity': qty,
                'price_unit': price_unit * factor,
            }))
            if credited:
                invoice_lines.append(self._prepare_allowance_discount_line(
                    category.name, credited, price * factor, service_product))

        if fee_lines:
            # One contract fee for the order, as in the order total
            rule = fee_lines[0]._get_billing_rule()
            if rule and getattr(rule, 'contract_id', 0):
                weight = sum(ln.weight or ln.estimated_weight or 0.0 for ln in fee_lines)
                invoice_lines += self._prepare_collection_fee_lines(
                    rule, weight, 1, fee_product,
                    self.env['wm.partner.contract'].browse(rule.contract_id).display_name)
        return invoice_lines

    def action_create_invoice(self):
        """
        Manually create a customer invoice (account.move) for this collection
        order, from its lines as priced on the order (see
        ``_prepare_direct_invoice_lines``).
        """
        self.ensure_one()
        # The invoice is created as superuser: only billing staff may trigger it
        if not self.env.su and not self.env['wm.billable.event']._can_create_invoices():
            raise AccessError(_("Only Billing & Finance users can create invoices from collection orders."))
        # Serialize concurrent invoicing of the same order, then re-read its state
        self.env.cr.execute("SELECT id FROM wm_collection_order WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['state', 'direct_invoice_id', 'is_billed', 'billing_run_line_id', 'consolidated_invoice_id'])
        if self.state not in ('completed', 'signed'):
            raise ValidationError(_("Invoices can only be created for completed or signed collection orders."))
        if self.is_billed or self.direct_invoice_id:
            raise ValidationError(_("Collection Order %s has already been billed.") % self.name)
        if not self.partner_id:
            raise ValidationError(_("Cannot generate invoice: No Customer specified on collection order."))

        today = fields.Date.context_today(self)
        # Invoice in the contract's currency (company currency without one)
        invoice_currency = self.contract_id.currency_id if self.contract_id else self.company_id.currency_id
        budget_of, remaining = self._get_allowance_budgets()
        used = {}
        invoice_lines = self._prepare_direct_invoice_lines(
            company_price_factor=self._get_invoice_currency_factor(invoice_currency, self.company_id, today),
            allowance=(budget_of, remaining, used))
        if not invoice_lines:
            raise ValidationError(_("No waste lines found to invoice on collection order %s.") % self.name)

        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': invoice_currency.id,
            'invoice_date': today,
            'ref': self.name,
            'invoice_line_ids': invoice_lines,
        })

        self.sudo().write({'direct_invoice_id': invoice.id})
        self._record_allowance_usage(budget_of, used)
        # Finance users have read-only access to orders: post as superuser
        self.sudo().message_post(body=_("Customer Invoice %s generated manually.") % invoice.name)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }


class WmCollectionOrderLine(models.Model):
    """Collection order lines priced on the order's own contract."""
    _inherit = 'wm.collection.order.line'

    # Same rule as in wm_collection, plus the order's contract (defined here)
    @api.depends('category_id', 'order_id.partner_id', 'order_id.scheduled_start', 'order_id.contract_id')
    def _compute_price_basis(self):
        return super()._compute_price_basis()
