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
from odoo.exceptions import AccessError, UserError, ValidationError


class WmBillableEvent(models.Model):
    """Model tracking ad-hoc billable events (extra pickup, overweight, contamination, emergency callout)."""
    _name = 'wm.billable.event'
    _description = 'Ad Hoc Billable Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc, id desc'

    name = fields.Char(string='Reference', default=lambda self: _('New'), copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True, index=True)
    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point', tracking=True)
    event_type = fields.Selection([
        ('extra_pickup', 'Extra Pickup'),
        ('overweight', 'Overweight Load'),
        ('contamination', 'Contaminated Load'),
        ('emergency_callout', 'Emergency Callout'),
    ], string='Event Type', required=True, tracking=True)
    event_date = fields.Date(string='Event Date', default=fields.Date.today, required=True, tracking=True)
    collection_order_id = fields.Many2one('wm.collection.order', string='Collection Order', tracking=True)
    portal_request_id = fields.Many2one('wm.portal.service.request', string='Portal Service Request', tracking=True)
    gate_entry_id = fields.Many2one('wm.facility.gate.entry', string='Facility Gate Entry', tracking=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    quantity = fields.Float(string='Quantity', default=1.0, help='e.g. kg over limit for overweight; 1 for flat-fee types')
    price_unit = fields.Monetary(string='Unit Price', compute='_compute_price_unit', store=True, readonly=False, currency_field='currency_id')
    discount_pct = fields.Float(
        string='Discount (%)', default=0.0, copy=False,
        help='Percentage discount on this event, e.g. the subscriber discount on extra pickups.')
    amount = fields.Monetary(string='Total Amount', compute='_compute_amount', store=True, currency_field='currency_id')
    rate_source = fields.Char(string='Rate Source / Rule', compute='_compute_price_unit', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line', readonly=True, copy=False)
    invoice_id = fields.Many2one('account.move', string='Invoice', compute='_compute_invoice_id', store=True, readonly=False, copy=False)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    notes = fields.Text(string='Notes')

    @api.depends('invoice_line_id', 'invoice_line_id.move_id')
    def _compute_invoice_id(self):
        for rec in self:
            if rec.invoice_line_id and rec.invoice_line_id.move_id:
                rec.invoice_id = rec.invoice_line_id.move_id
            elif not rec.invoice_id:
                rec.invoice_id = False

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = 1 if rec.invoice_id else 0

    def action_view_invoice(self):
        self.ensure_one()
        invoice = self.invoice_id or (self.invoice_line_id.move_id if self.invoice_line_id else False)
        if not invoice:
            return None
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.billable.event') or _('New')
        return super().create(vals_list)

    @api.depends('event_type', 'partner_id', 'event_date', 'quantity', 'company_id')
    def _compute_price_unit(self):
        for event in self:
            if not event.event_type or not event.event_date:
                event.price_unit = 0.0
                event.rate_source = ''
                continue
            Rule = self.env['wm.event.pricing.rule']
            base_domain = [
                ('event_type', '=', event.event_type),
                ('active', '=', True),
                ('company_id', 'in', (False, event.company_id.id)),
                ('effective_date', '<=', event.event_date),
                '|', ('expiry_date', '=', False), ('expiry_date', '>=', event.event_date),
            ]
            rule = Rule.search(base_domain + [('partner_id', '=', event.partner_id.id)], limit=1, order='sequence asc, id desc') \
                or Rule.search(base_domain + [('partner_id', '=', False)], limit=1, order='sequence asc, id desc')
            if rule:
                price = rule.price_unit
                if rule.min_charge and (price * (event.quantity or 1.0)) < rule.min_charge:
                    price = rule.min_charge / (event.quantity or 1.0)
                event.price_unit = price
                event.rate_source = rule.name or f"Rule #{rule.id}"
            else:
                event.price_unit = 0.0
                event.rate_source = _('No matching rule — manual price required')

    @api.constrains('quantity')
    def _check_quantity_positive(self):
        for event in self:
            if event.quantity <= 0:
                raise ValidationError(_("The quantity of a billable event must be greater than zero."))

    @api.depends('quantity', 'price_unit', 'discount_pct')
    def _compute_amount(self):
        for event in self:
            gross = (event.quantity or 0.0) * (event.price_unit or 0.0)
            event.amount = gross * (1.0 - min(max(event.discount_pct or 0.0, 0.0), 100.0) / 100.0)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only draft billable events can be confirmed."))
            rec.write({'state': 'confirmed'})

    @api.model
    def _can_create_invoices(self):
        """Billing staff allowed to create customer invoices from WM records."""
        user = self.env.user
        return user.has_group('wm_base.group_wm_finance') or user.has_group('account.group_account_manager')

    def _prepare_invoice_line_vals(self):
        """Invoice line values for this event."""
        self.ensure_one()
        event_label = dict(self._fields['event_type'].selection).get(self.event_type, self.event_type)
        return {
            'name': _("%(type)s — %(date)s (Ref: %(ref)s)") % {
                'type': event_label,
                'date': self.event_date.strftime('%d/%m/%Y') if self.event_date else '',
                'ref': self.name,
            },
            'quantity': self.quantity or 1.0,
            'price_unit': self.price_unit,
            'discount': min(max(self.discount_pct or 0.0, 0.0), 100.0),
        }

    def action_create_invoice(self):
        self.ensure_one()
        # The invoice is created as superuser: only billing staff may trigger it
        if not self.env.su and not self._can_create_invoices():
            raise AccessError(_("Only Billing & Finance users can invoice billable events."))
        # Serialize concurrent clicks / cron runs, then re-read before deciding
        self.env.cr.execute("SELECT id FROM wm_billable_event WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['state', 'invoice_id', 'invoice_line_id'])
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed billable events can be invoiced."))
        if self.invoice_line_id:
            raise UserError(_("This billable event is already invoiced."))

        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            # The price comes from the event pricing rule, in the event's currency
            'currency_id': (self.currency_id or self.company_id.currency_id).id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, self._prepare_invoice_line_vals())],
        })
        self.sudo().write({
            'state': 'invoiced',
            'invoice_id': invoice.id,
            'invoice_line_id': invoice.invoice_line_ids[0].id if invoice.invoice_line_ids else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        for rec in self:
            if rec.state == 'invoiced' or rec.invoice_line_id:
                raise UserError(_("Cannot cancel an invoiced billable event. Cancel or credit its invoice first."))
            rec.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'invoiced':
                raise ValidationError(_("Cannot reset an invoiced billable event to draft."))
            rec.write({'state': 'draft'})


class WasteBatchInspectionInherit(models.Model):
    _inherit = 'wm.batch.inspection'

    contamination_event_id = fields.Many2one(
        'wm.billable.event',
        string='Contamination Billable Event',
        readonly=True,
        copy=False,
        help='Billable event auto-generated when this inspection failed due to contamination.'
    )


class WmFacilityGateEntryBillingExt(models.Model):
    _inherit = 'wm.facility.gate.entry'

    billable_event_ids = fields.One2many(
        'wm.billable.event',
        'gate_entry_id',
        string='Billable Events'
    )


class WmFacilityGateEntryRejectionLineBillingExt(models.Model):
    _inherit = 'wm.facility.gate.entry.rejection.line'

    billable_event_id = fields.Many2one(
        'wm.billable.event',
        string='Generated Billable Event',
        readonly=True,
        copy=False,
        ondelete='set null'
    )
