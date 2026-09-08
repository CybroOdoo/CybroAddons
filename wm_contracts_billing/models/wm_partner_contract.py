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
import calendar
import collections
from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class WmPartnerContract(models.Model):
    """Waste management service contract governing billing terms, collection schedules, and SLAs."""
    _name = 'wm.partner.contract'
    _description = 'Waste Management Contract for Partner'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    # Field Declarations
    name = fields.Char(string='Name', default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )
    from_date = fields.Date(
        string='From Date',
        required=True,
        default=fields.Date.today()
    )
    to_date = fields.Date(string='To Date', required=True)
    contract_line_ids = fields.One2many(
        'wm.partner.contract.line',
        'contract_id',
        string='Contract Lines',
        required=True
    )
    selected_product_ids = fields.Many2many(
        'wm.waste.category',
        compute='_compute_selected_product_ids',
        string='Selected Products'
    )
    collection_point_ids = fields.Many2many(
        'wm.collection.point',
        string='Sites',
        required=True,
        domain="[('partner_id', '=', partner_id)]",
        help="Collection sites covered by this contract."
    )
    collection_point_count = fields.Integer(compute='_compute_collection_point_count')
    sla_id = fields.Many2one('wm.sla', string='SLA', required=True)
    template_id = fields.Many2one(
        'wm.signature.template',
        string='Signature Template',
        help="Select signature template for this contract."
    )
    sla_snapshot_html = fields.Html(
        string='SLA Terms (Snapshot)',
        readonly=True,
        copy=False,
        help="Frozen copy of the SLA's terms at the moment this contract was "
             "confirmed. The report and portal always show this snapshot once "
             "it exists, so editing the SLA master record afterward never "
             "changes what an already-confirmed contract displays."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Frequency', required=True)
    no_of_frequency = fields.Integer(
        string='No of Frequency',
        required=True,
        help='Number of collections per frequency period — e.g. 3 means '
             '3 times per day (daily), 3 times per week (weekly), or '
             '3 times per month (monthly).'
    )
    monday = fields.Boolean(string='Mon')
    tuesday = fields.Boolean(string='Tue')
    wednesday = fields.Boolean(string='Wed')
    thursday = fields.Boolean(string='Thu')
    friday = fields.Boolean(string='Fri')
    saturday = fields.Boolean(string='Sat')
    sunday = fields.Boolean(string='Sun')
    monthly_option = fields.Selection([
        ('date', 'Specific Day of Month'),
        ('last_day', 'Last Day of Month'),
    ], string='Monthly Schedule Option', default='date')
    day_of_month = fields.Integer(string='Day of Month', default=1, help='Day of the month for collection (1-31).')
    last_generated_date = fields.Date(string='Last Generated Date')
    signature_signer_count = fields.Integer(string='Signatures', compute='_compute_signature_signer_count')
    next_signer_id = fields.Many2one('wm.signature.request.signer', compute='_compute_next_signer', string='Next Signer')
    next_signer_role_name = fields.Char(compute='_compute_next_signer', string='Next Signer Role')
    billing_basis = fields.Selection([
        ('per_collection', 'Per Collection'),
        ('material', 'Per Material'),
        ('hybrid', 'Base Fee + Material Overage'),
        ('category_rate', 'Per Category Rate'),
    ], string='Billing', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    fixed_price = fields.Monetary(string='Fixed Price per Collection', currency_field='currency_id')
    max_weight = fields.Float(string='Maximum Weight (kg)')
    overweight_price = fields.Monetary(string='Overweight Price per 10kg', currency_field='currency_id')
    included_weight = fields.Float(
        string='Included Weight per Collection (kg)',
        help="Weight covered by the fixed fee before material-based "
             "overage charges apply. Only used when Billing is "
             "'Base Fee + Material Overage'."
    )
    is_from_date_passed = fields.Boolean(
        compute='_compute_is_from_date_passed',
        string='From Date Passed',
        store=False
    )

    # Compute, Inverse, and Search Methods
    @api.depends('contract_line_ids.category_id')
    def _compute_selected_product_ids(self):
        """
        Compute the waste category IDs selected in the contract lines.
        """
        for contract in self:
            contract.selected_product_ids = contract.contract_line_ids.category_id.ids

    @api.depends('collection_point_ids')
    def _compute_collection_point_count(self):
        """
        Compute the total number of collection points assigned to this
        contract.
        """
        for contract in self:
            contract.collection_point_count = len(contract.collection_point_ids)

    def _compute_signature_signer_count(self):
        """
        Compute the total number of signers associated with the contract's
        signature requests.
        """
        saved_contracts = self.filtered(lambda c: bool(c.id) and isinstance(c.id, int))
        if not saved_contracts:
            for contract in self:
                contract.signature_signer_count = 0
            return

        ref_docs = [f"wm.partner.contract,{contract.id}" for contract in saved_contracts]
        requests = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', 'in', ref_docs),
            ('state', '!=', 'cancel')
        ])
        signer_count_by_contract = {}
        for req in requests:
            try:
                cid = int(str(req.reference_doc).split(',')[1])
                signer_count_by_contract[cid] = signer_count_by_contract.get(cid, 0) + len(req.signer_ids)
            except (ValueError, IndexError, AttributeError):
                continue

        for contract in self:
            contract.signature_signer_count = signer_count_by_contract.get(contract.id, 0)

    def _compute_next_signer(self):
        """
        Compute the next pending signer ID and role name for the signature
        request.
        """
        saved_contracts = self.filtered(lambda c: bool(c.id) and isinstance(c.id, int))
        if not saved_contracts:
            for contract in self:
                contract.next_signer_id = False
                contract.next_signer_role_name = False
            return

        ref_docs = [f"wm.partner.contract,{contract.id}" for contract in saved_contracts]
        requests = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', 'in', ref_docs),
            ('state', '=', 'sent')
        ])
        requests_by_contract = {}
        for req in requests:
            try:
                cid = int(str(req.reference_doc).split(',')[1])
                requests_by_contract.setdefault(cid, self.env['wm.signature.request']).concat(req)
            except (ValueError, IndexError, AttributeError):
                continue

        for contract in self:
            reqs = requests_by_contract.get(contract.id, self.env['wm.signature.request'])
            pending_signers = reqs.mapped('signer_ids').filtered(lambda s: s.state != 'signed')
            if len(pending_signers) == 1 and 'manager' not in (pending_signers[0].role_id.name or '').lower():
                contract.next_signer_id = pending_signers[0].id
                contract.next_signer_role_name = pending_signers[0].role_id.name
            else:
                contract.next_signer_id = False
                contract.next_signer_role_name = False

    @api.depends('from_date')
    def _compute_is_from_date_passed(self):
        """
        Check whether the contract start date has passed, enabling the
        'Activate' button on the contract form and preventing premature
        contract activation.
        """
        today = fields.Date.today()
        for contract in self:
            contract.is_from_date_passed = bool(contract.from_date and contract.from_date < today)

    # Constrains and Onchange Methods
    @api.constrains('collection_point_ids', 'state')
    def _check_unique_active_contract_per_site(self):
        """
        Ensure that each collection point has only one active or confirmed
        contract at any time.
        """
        for contract in self:
            if contract.collection_point_ids and contract.state in ('confirmed', 'sent', 'signed', 'ongoing'):
                for site in contract.collection_point_ids:
                    domain = [
                        ('collection_point_ids', 'in', [site.id]),
                        ('state', 'in', ('confirmed', 'sent', 'signed', 'ongoing')),
                        ('id', '!=', contract.id),
                    ]
                    existing_contracts = self.search(domain)
                    if existing_contracts:
                        raise ValidationError(_(
                            "The site '%(site_name)s' already has an active or confirmed contract (Reference: %(ref)s).",
                            site_name=site.name,
                            ref=', '.join(existing_contracts.mapped('name')),
                        ))

    @api.constrains('partner_id', 'collection_point_ids', 'state', 'from_date', 'to_date')
    def _check_unique_contract_per_customer(self):
        """
        Ensure that a customer does not have multiple conflicting ongoing
        contracts covering the same timeframe and sites.
        """
        for contract in self:
            if not contract.partner_id or contract.state not in ('confirmed', 'ongoing'):
                continue
            domain = [
                ('partner_id', '=', contract.partner_id.id),
                ('state', '=', contract.state),
                ('id', '!=', contract.id),
            ]
            if contract.from_date and contract.to_date:
                domain += [
                    ('from_date', '<=', contract.to_date),
                    ('to_date', '>=', contract.from_date),
                ]
            conflicts = self.search(domain)
            if contract.collection_point_ids:
                conflicts = conflicts.filtered(lambda c: bool(set(c.collection_point_ids.ids).intersection(contract.collection_point_ids.ids)))
            if conflicts:
                raise ValidationError(_(
                    "The customer '%(customer_name)s' already has an overlapping active contract for the same sites (Reference: %(ref)s).",
                    customer_name=contract.partner_id.name,
                    ref=', '.join(conflicts.mapped('name')),
                ))

    @api.constrains('from_date', 'to_date')
    def _check_dates(self):
        """
        Validate that the contract start date is not after the contract end
        date.
        """
        for contract in self:
            if contract.from_date and contract.to_date and contract.to_date < contract.from_date:
                raise ValidationError(_("The End Date (To Date) cannot be before the Start Date (From Date)."))

    @api.constrains('fixed_price', 'max_weight', 'overweight_price', 'included_weight', 'billing_basis', 'contract_line_ids')
    def _check_pricing_values(self):
        """
        Validate pricing constraints for per_collection, hybrid, category_rate,
        and material billing basis.
        """
        for contract in self:
            if contract.billing_basis == 'per_collection':
                if contract.fixed_price <= 0:
                    raise ValidationError(_("Fixed Price per Collection must be greater than zero."))
                if contract.max_weight <= 0:
                    raise ValidationError(_("Maximum Weight (kg) must be greater than zero."))
                if contract.overweight_price <= 0:
                    raise ValidationError(_("Overweight Price per 10kg must be greater than zero."))
            elif contract.billing_basis == 'hybrid':
                if contract.fixed_price <= 0:
                    raise ValidationError(_("Fixed Price per Collection must be greater than zero."))
                if contract.included_weight <= 0:
                    raise ValidationError(_("Included Weight per Collection must be greater than zero."))
            elif contract.billing_basis == 'category_rate':
                if not contract.contract_line_ids:
                    raise ValidationError(_("Add at least one waste category line before using category-rate billing."))
                if any(line.price <= 0 for line in contract.contract_line_ids):
                    raise ValidationError(_("Every waste category line must have a Rate per kg greater than zero."))
            elif contract.billing_basis == 'material':
                if not contract.contract_line_ids:
                    raise ValidationError(_(
                        "Add at least one waste category line before using material-based billing."
                    ))
                if any(line.price < 0 for line in contract.contract_line_ids):
                    raise ValidationError(_("Rate per kg cannot be negative."))

    @api.constrains('no_of_frequency', 'frequency')
    def _check_no_of_frequency(self):
        """
        Validate that the number of frequency is strictly positive and within
        valid period bounds.
        """
        limits = {'daily': 10, 'weekly': 7, 'monthly': 31}
        for contract in self:
            if contract.no_of_frequency <= 0:
                raise ValidationError(_("The 'No of Frequency' must be strictly greater than 0."))
            if contract.frequency in limits and contract.no_of_frequency > limits[contract.frequency]:
                raise ValidationError(_(
                    "The 'No of Frequency' (%(num)s) exceeds the maximum allowed limit (%(max)s) for %(freq)s frequency.",
                    num=contract.no_of_frequency,
                    max=limits[contract.frequency],
                    freq=contract.frequency,
                ))

    @api.constrains('day_of_month', 'monthly_option', 'frequency')
    def _check_monthly_schedule(self):
        """
        Validate day_of_month bounds when monthly frequency is configured.
        """
        for contract in self:
            if contract.frequency == 'monthly' and contract.monthly_option == 'date':
                if not (1 <= contract.day_of_month <= 31):
                    raise ValidationError(_("Day of Month must be between 1 and 31."))

    @api.onchange('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'frequency')
    def _onchange_weekdays(self):
        """
        Automatically set no_of_frequency based on selected weekly collection
        days.
        """
        if self.frequency == 'weekly':
            selected_days = sum([
                self.monday, self.tuesday, self.wednesday,
                self.thursday, self.friday, self.saturday, self.sunday
            ])
            if selected_days > 0:
                self.no_of_frequency = selected_days

    # CRUD Methods (ORM Overrides)
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to generate sequence numbers for new contracts.
        """
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.partner.contract')
        return super().create(vals_list)

    def message_post(self, **kwargs):
        """
        Override message_post to transition draft contracts to sent state and
        record SLA snapshot when email is sent.
        """
        if self.env.context.get('mark_contract_as_sent'):
            for contract in self:
                vals = {}
                if contract.state == 'draft':
                    vals['state'] = 'sent'
                if contract.sla_id:
                    vals['sla_snapshot_html'] = contract._build_sla_snapshot_html()
                contract.write(vals)
        return super().message_post(**kwargs)

    def action_confirm(self):
        """
        Confirm the contract using the frozen snapshot of the SLA terms.
        """
        if any(c.state != 'signed' for c in self):
            raise UserError(_("Only contracts in 'Signed' state can be confirmed."))
        today = fields.Date.today()
        for contract in self:
            if contract.to_date and contract.to_date < today:
                raise ValidationError(_("Cannot confirm contract '%s' because its end date (%s) has already passed.") % (contract.name, contract.to_date))
            if not (contract.contract_line_ids and contract.sla_id):
                raise ValidationError(_('Select at least one waste type, SLA, and Collection point.'))

            vals = {'state': 'confirmed'}
            if not contract.sla_snapshot_html:
                vals['sla_snapshot_html'] = contract._build_sla_snapshot_html()
            contract.write(vals)

    def get_portal_signature_url(self):
        """
        Generate a time-limited, signed portal URL for the contract's digital
        signature page, enabling partners to countersign the contract without
        logging into the backend.
        """
        self.ensure_one()
        sig_request = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', '=', f'wm.partner.contract,{self.id}'),
            ('state', '!=', 'cancel')
        ], limit=1)
        if not sig_request and self.state in ('draft', 'sent'):
            role = self.env['wm.signature.role'].sudo().search([('name', 'ilike', 'customer')], limit=1)
            if not role:
                role = self.env['wm.signature.role'].sudo().search([], limit=1)
            if not role:
                role = self.env['wm.signature.role'].sudo().create({'name': 'Customer'})

            signer_partner = self.partner_id
            if signer_partner and signer_partner.email:
                sig_request = self.env['wm.signature.request'].sudo().create({
                    'template_id': self.template_id.id if self.template_id else False,
                    'reference_doc': f'wm.partner.contract,{self.id}',
                    'signer_ids': [(0, 0, {
                        'partner_id': signer_partner.id,
                        'role_id': role.id,
                        'email': signer_partner.email,
                    })],
                })
                sig_request.sudo().write({'state': 'sent'})

        if sig_request:
            signer = sig_request.signer_ids.filtered(lambda s: s.partner_id == self.partner_id and s.state != 'signed')[:1]
            if not signer:
                signer = sig_request.signer_ids.filtered(lambda s: s.state != 'signed')[:1]
            if signer:
                return f"/wm_signature/sign/{signer.access_token}"
        return ''

    def action_send(self):
        """
        Send the contract document to the client contact via email, attach the
        PDF preview, and transition the contract to 'sent' state awaiting
        counterpart signature.
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_("The contract can only be sent when it is in Draft or Sent state."))
        if not self.template_id:
            raise ValidationError(_("Select a Signature Template before sending the contract."))
        if not self.contract_line_ids:
            raise ValidationError(_("Select at least one waste type (contract line) before sending the contract."))
        if not self.sla_id:
            raise ValidationError(_("Select an SLA before sending the contract."))
        partner = self.partner_id
        if not partner.email:
            raise ValidationError(_(
                "The customer %s does not have an email address configured."
            ) % partner.name)

        # Create signature request if it doesn't exist
        sig_request = self.env['wm.signature.request'].search([
            ('reference_doc', '=', f'wm.partner.contract,{self.id}'),
            ('state', '!=', 'cancel')
        ], limit=1)

        if not sig_request:
            roles = self.template_id.role_ids
            if not roles:
                role = self.env['wm.signature.role'].search([], limit=1)
                if not role:
                    role = self.env['wm.signature.role'].create({'name': 'Signer'})
                roles = role

            signer_vals = []
            for role in roles:
                role_name_lower = (role.name or '').lower()
                signer_partner = False
                if 'customer' in role_name_lower or 'client' in role_name_lower:
                    signer_partner = self.partner_id or role.partner_id
                elif 'manager' in role_name_lower or 'company' in role_name_lower or 'admin' in role_name_lower:
                    signer_partner = role.partner_id or self.env.user.partner_id
                else:
                    signer_partner = role.partner_id or self.partner_id

                if not signer_partner:
                    signer_partner = self.partner_id

                if not signer_partner.email:
                    raise ValidationError(_(
                        "The signer %s (Role: %s) does not have an email address configured. "
                        "All signers must have a valid email to receive the signature request."
                    ) % (signer_partner.name, role.name))

                signer_vals.append((0, 0, {
                    'partner_id': signer_partner.id,
                    'role_id': role.id,
                    'email': signer_partner.email,
                }))

            sig_request = self.env['wm.signature.request'].create({
                'template_id': self.template_id.id,
                'reference_doc': f'wm.partner.contract,{self.id}',
                'signer_ids': signer_vals,
            })
            sig_request.write({'state': 'sent'})

        template = self.env.ref(
            'wm_contracts_billing.email_template_wm_contract_send',
            raise_if_not_found=False
        )

        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form',
            raise_if_not_found=False
        )

        mail_server = self.env['ir.mail_server'].sudo().search(
            [('active', '=', True)], order='sequence asc', limit=1
        )

        ctx = {
            'default_model': 'wm.partner.contract',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_template_id': template.id if template else False,
            'mark_contract_as_sent': True,
            'default_mail_server_id': mail_server.id if mail_server else False,
            'default_partner_ids': [self.partner_id.id] if self.partner_id else [],
        }

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id if compose_form else False, 'form')],
            'view_id': compose_form.id if compose_form else False,
            'target': 'new',
            'context': ctx,
        }

    def action_sign_next(self):
        """
        Direct the next pending signer to their portal signing interface.
        """
        self.ensure_one()
        if self.next_signer_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/wm_signature/sign/{self.next_signer_id.access_token}',
                'target': 'self',
            }
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_view_signatures(self):
        """
        Return window action to view details of all signature requests for this
        contract.
        """
        self.ensure_one()
        requests = self.env['wm.signature.request'].search([
            ('reference_doc', '=', f"wm.partner.contract,{self.id}"),
            ('state', '!=', 'cancel')
        ])
        signers = requests.mapped('signer_ids')
        return {
            'name': _('Signatures'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.signature.request.signer',
            'view_mode': 'list',
            'domain': [('id', 'in', signers.ids)],
            'context': {'create': False, 'edit': False},
        }

    def action_create_collection_point(self):
        """
        Open window action to create a new collection point for this contract's
        customer.
        """
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please select a customer first before creating a collection point."))
        return {
            'name': _('Create Collection Point'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.collection.point',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_street': self.partner_id.street,
                'default_city': self.partner_id.city,
                'default_state_id': self.partner_id.state_id.id if self.partner_id.state_id else False,
                'default_zip': self.partner_id.zip,
                'default_country_id': self.partner_id.country_id.id if self.partner_id.country_id else False,
                'default_name': f"{self.partner_id.name} - Collection Point",
            },
        }

    def action_view_collection_point(self):
        """
        Return window action to view or create collection points for this
        contract's customer.
        """
        self.ensure_one()
        domain = [('partner_id', '=', self.partner_id.id)] if self.partner_id else [('id', 'in', self.collection_point_ids.ids)]
        return {
            'name': _('Collection Points'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.collection.point',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'default_partner_id': self.partner_id.id if self.partner_id else False},
        }

    def action_start(self):
        """
        Activate the contract and transition it to 'ongoing' status after
        verifying that the start date has passed and all required fields are
        populated.
        """
        if any(c.state != 'confirmed' for c in self):
            raise UserError(_("Only confirmed contracts can be started."))
        self.write({'state': 'ongoing'})

    def action_cancel(self):
        """
        Cancel the waste management service contract, releasing all allocated
        collection points and notifying the partner of the cancellation with a
        reason.
        """
        if any(c.state in ('cancelled', 'expired') for c in self):
            raise UserError(_("This contract is already cancelled or expired."))
        self._cancel_pending_signature_requests()
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """
        Reset the contract to draft state so terms, pricing basis, or
        collection point assignments can be corrected before re-sending to the
        client.
        """
        if any(c.state != 'cancelled' for c in self):
            raise UserError(_("Only cancelled contracts can be reset to draft."))
        self._cancel_pending_signature_requests()
        self.write({'state': 'draft'})

    def _cancel_pending_signature_requests(self):
        """
        Cancel any non-cancelled signature requests linked to these contracts
        so that a         subsequent action_send starts a fresh signature
        request rather than reusing an old         one whose signers may
        already be fully signed (which would leave no pending signer,
        and therefore no sign link, in the outgoing email).
        """
        for contract in self:
            requests = self.env['wm.signature.request'].search([
                ('reference_doc', '=', f'wm.partner.contract,{contract.id}'),
                ('state', '!=', 'cancel'),
            ])
            if requests:
                requests.write({'state': 'cancel'})

    # Other Business / Helper / Cron Methods
    def _build_sla_snapshot_html(self):
        """
        Render the selected SLA commits and penalty terms into a frozen HTML
        blob at confirmation.
        """
        self.ensure_one()
        sla = self.sla_id
        if not sla:
            return False

        uom_labels = dict(self.env['wm.sla.line']._fields['uom'].selection)
        type_labels = dict(self.env['wm.sla.line']._fields['sla_type'].selection)
        penalty_labels = dict(self.env['wm.sla.line']._fields['penalty_type'].selection)

        rows = []
        for line in sla.sla_line_ids:
            target = '-'
            if line.target_value:
                target = f"{line.target_value:g} {uom_labels.get(line.uom, '') or ''}".strip()
            penalty = penalty_labels.get(line.penalty_type, '') or '-'
            if line.penalty_type in ('fixed_credit', 'percentage_credit') and line.penalty_value:
                suffix = '%' if line.penalty_type == 'percentage_credit' else ''
                penalty = f"{penalty}: {line.penalty_value:g}{suffix}"
            rows.append(Markup(
                "<tr>"
                "<td style='padding:6px 10px; border:1px solid #dce6f5;'>{type}</td>"
                "<td style='padding:6px 10px; border:1px solid #dce6f5;'>{desc}</td>"
                "<td style='padding:6px 10px; border:1px solid #dce6f5;'>{target}</td>"
                "<td style='padding:6px 10px; border:1px solid #dce6f5;'>{penalty}</td>"
                "</tr>"
            ).format(
                type=type_labels.get(line.sla_type, line.sla_type),
                desc=line.description or '',
                target=target,
                penalty=penalty,
            ))

        table_html = Markup("")
        if rows:
            table_html = Markup(
                "<table style='width:100%; border-collapse:collapse; margin:10px 0;'>"
                "<thead><tr>"
                "<th style='text-align:left; padding:6px 10px; border:1px solid #dce6f5;'>Type</th>"
                "<th style='text-align:left; padding:6px 10px; border:1px solid #dce6f5;'>Commitment</th>"
                "<th style='text-align:left; padding:6px 10px; border:1px solid #dce6f5;'>Target</th>"
                "<th style='text-align:left; padding:6px 10px; border:1px solid #dce6f5;'>Penalty</th>"
                "</tr></thead><tbody>{rows}</tbody></table>"
            ).format(rows=Markup('').join(rows))

        return Markup("<h4>{name}</h4>{table}<div>{terms}</div>").format(
            name=sla.name or '',
            table=table_html,
            terms=Markup(sla.terms_and_conditions) if sla.terms_and_conditions else Markup(""),
        )

    def get_expiry_status(self):
        """
        Evaluate the active contract timeframe status (expired, pending, or
        active).
        """
        self.ensure_one()
        today = fields.Date.today()
        if self.to_date and self.to_date < today:
            return 'expired'
        elif self.from_date and self.from_date > today:
            return 'pending'
        return 'active'

    def _get_report_base_filename(self):
        """
        Define the default filename pattern when generating the contract report
        PDF.
        """
        self.ensure_one()
        return self.name

    @api.model
    def _cron_expire_contracts(self):
        """
        Cron action to transition all contracts whose end date has passed into
        expired state.
        """
        today = fields.Date.today()
        expiring = self.search([
            ('to_date', '<', today),
            ('state', 'in', ('confirmed', 'sent', 'signed', 'ongoing')),
        ])
        if expiring:
            expiring.write({'state': 'expired'})

    @api.model
    def _cron_generate_collection_orders(self):
        """
        Cron action to auto-generate recurring collection orders based on
        contract frequencies.
        """
        today = fields.Date.today()
        contracts = self.search([('state', '=', 'ongoing')])

        for contract in contracts:
            if not contract.collection_point_ids or not contract.frequency:
                continue

            # Ensure contract is within valid active dates
            if (contract.from_date and today < contract.from_date) or (contract.to_date and today > contract.to_date):
                continue

            # Check if collection order generation is due based on contract schedule
            if not self._is_contract_due(contract, today):
                continue

            num = contract.no_of_frequency or 1

            if contract.frequency == 'daily':
                period_start = today
                period_end = today
            elif contract.frequency == 'weekly':
                period_start = today - timedelta(days=today.weekday())
                period_end = period_start + timedelta(days=6)
            elif contract.frequency == 'monthly':
                period_start = today.replace(day=1)
                period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)
            else:
                continue

            start_dt = datetime.combine(period_start, time.min)
            end_dt = datetime.combine(period_end, time.max)

            existing_orders = self.env['wm.collection.order'].search([
                ('contract_id', '=', contract.id),
                ('scheduled_start', '>=', start_dt),
                ('scheduled_start', '<=', end_dt),
            ])

            site_order_counts = collections.Counter(existing_orders.mapped('collection_point_id.id'))
            for site in contract.collection_point_ids:
                site_existing_count = site_order_counts.get(site.id, 0)
                if site_existing_count < num:
                    to_create_count = num - site_existing_count

                    scheduled_dates = []

                    if contract.frequency == 'weekly':
                        weekday_flags = [
                            contract.monday, contract.tuesday, contract.wednesday,
                            contract.thursday, contract.friday, contract.saturday, contract.sunday
                        ]
                        selected_weekdays = [idx for idx, flag in enumerate(weekday_flags) if flag]
                        if selected_weekdays:
                            curr_date = period_start
                            while curr_date <= period_end:
                                if curr_date.weekday() in selected_weekdays and curr_date >= today:
                                    scheduled_dates.append(curr_date)
                                curr_date += timedelta(days=1)

                    elif contract.frequency == 'monthly':
                        if contract.monthly_option == 'last_day':
                            target_date = period_end
                            if target_date >= today:
                                scheduled_dates.append(target_date)
                        elif contract.monthly_option == 'date' and contract.day_of_month:
                            max_days = calendar.monthrange(period_start.year, period_start.month)[1]
                            target_day = min(contract.day_of_month, max_days)
                            target_date = period_start.replace(day=target_day)
                            if target_date >= today:
                                scheduled_dates.append(target_date)

                    if not scheduled_dates:
                        remaining_dates = []
                        curr_date = today
                        while curr_date <= period_end:
                            remaining_dates.append(curr_date)
                            curr_date += timedelta(days=1)

                        if not remaining_dates:
                            continue

                        for j in range(to_create_count):
                            idx = (j * len(remaining_dates)) // to_create_count
                            scheduled_dates.append(remaining_dates[idx])
                    else:
                        scheduled_dates = scheduled_dates[:to_create_count]

                    if contract.frequency == 'daily' and to_create_count > 1:
                        total_seconds = 8 * 3600  # 8 hours working window (09:00 to 17:00)
                        step_seconds = total_seconds / to_create_count
                        for idx, sched_date in enumerate(scheduled_dates):
                            start_offset = idx * step_seconds
                            end_offset = (idx + 1) * step_seconds
                            base_dt = datetime.combine(sched_date, time(9, 0, 0))
                            sched_start = base_dt + timedelta(seconds=start_offset)
                            sched_end = base_dt + timedelta(seconds=end_offset)
                            self.env['wm.collection.order'].create({
                                'partner_id': contract.partner_id.id,
                                'collection_point_id': site.id,
                                'contract_id': contract.id,
                                'scheduled_start': sched_start,
                                'scheduled_end': sched_end,
                                'state': 'draft',
                            })
                    else:
                        for sched_date in scheduled_dates:
                            sched_start = datetime.combine(sched_date, time(9, 0, 0))
                            sched_end = datetime.combine(sched_date, time(17, 0, 0))
                            self.env['wm.collection.order'].create({
                                'partner_id': contract.partner_id.id,
                                'collection_point_id': site.id,
                                'contract_id': contract.id,
                                'scheduled_start': sched_start,
                                'scheduled_end': sched_end,
                                'state': 'draft',
                            })

            contract.write({'last_generated_date': today})

    @api.model
    def _is_contract_due(self, contract, today):
        """
        Helper to determine if a contract requires new collection order
        generation for the target period.
        """
        if not contract.last_generated_date:
            return contract.from_date and today >= contract.from_date

        last = contract.last_generated_date

        if contract.frequency == 'daily':
            return today > last
        elif contract.frequency == 'weekly':
            current_period_start = today - timedelta(days=today.weekday())
            return last < current_period_start
        elif contract.frequency == 'monthly':
            current_period_start = today.replace(day=1)
            return last < current_period_start
        else:
            return False

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string='Source Opportunity',
        copy=False,
        readonly=True,
        ondelete='set null',
        help='The CRM opportunity this contract was converted from.',
        index=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Quotation / Order',
        copy=False,
        readonly=True,
        ondelete='set null',
        help='The Sales quotation / order this contract was converted from.',
        index=True,
    )
    originated_from_crm = fields.Boolean(
        string='Created from CRM / Quotation',
        compute='_compute_originated_from_crm',
        store=True,
    )

    @api.depends('crm_lead_id', 'sale_order_id')
    def _compute_originated_from_crm(self):
        """
        True if the contract was created via CRM lead or Quotation conversion.
        """
        for contract in self:
            contract.originated_from_crm = bool(contract.crm_lead_id or contract.sale_order_id)

    def action_view_source_lead(self):
        """
        Smart button: open the originating CRM opportunity form.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Source Opportunity'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.crm_lead_id.id,
        }

    def action_view_source_sale_order(self):
        """
        Smart button: open the originating Sales Quotation / Order form.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Source Quotation'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }
