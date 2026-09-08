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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WmLeadConversionWizard(models.TransientModel):
    """Wizard to convert a won CRM opportunity into a draft waste management service contract."""
    _name = 'wm.lead.conversion.wizard'
    _description = 'Convert CRM Lead to WM Contract'

    # ------------------------------------------------------------------
    # Source fields (read-only — set from context by the calling action)
    # ------------------------------------------------------------------
    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        readonly=True,
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Quotation / Order',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Warning banner: existing active contract for this customer
    # ------------------------------------------------------------------
    has_existing_contract = fields.Boolean(
        string='Has Existing Active Contract',
        readonly=True,
        help='Set to True when the customer already has an active/sent/signed '
             'contract. Surfaces a warning banner in the wizard — does NOT '
             'block creation of the new draft contract.',
    )
    existing_contract_name = fields.Char(
        string='Existing Contract Reference',
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Service context (pre-filled from lead, display-only)
    # ------------------------------------------------------------------
    service_type = fields.Selection([
        ('collection', 'Waste Collection'),
        ('recycling', 'Recycling Services'),
        ('both', 'Collection + Recycling'),
        ('hazardous', 'Hazardous Waste Handling'),
        ('other', 'Other'),
    ], string='Service Type', readonly=True)

    # ------------------------------------------------------------------
    # Contract terms to confirm / complete before creation
    # ------------------------------------------------------------------
    contract_from_date = fields.Date(
        string='Contract Start Date',
        required=True,
        default=fields.Date.today,
    )
    contract_to_date = fields.Date(
        string='Contract End Date',
        required=True,
    )
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Collection Frequency', required=True, default='weekly')
    no_of_frequency = fields.Integer(
        string='Collections per Period',
        required=True,
        default=1,
        help='Number of collections per frequency period, e.g. 3 means '
             '3 times per week (weekly) or 3 times per month (monthly).',
    )
    billing_basis = fields.Selection([
        ('per_collection', 'Per Collection'),
        ('material', 'Per Material'),
        ('hybrid', 'Base Fee + Material Overage'),
        ('category_rate', 'Per Category Rate'),
    ], string='Billing Basis', required=True, default='per_collection')
    sla_id = fields.Many2one(
        'wm.sla',
        string='SLA',
        required=True
    )
    fixed_price = fields.Float(
        string='Fixed Price per Collection',
        default=100.0,
        help='Fixed fee charged per collection.'
    )
    max_weight = fields.Float(
        string='Maximum Weight (kg)',
        default=500.0,
        help='Maximum weight per collection before overweight rates apply.'
    )
    overweight_price = fields.Float(
        string='Overweight Price per 10kg',
        default=10.0,
        help='Overage charge per 10kg over max weight.'
    )
    included_weight = fields.Float(
        string='Included Weight per Collection (kg)',
        default=100.0,
        help='Included weight per collection for hybrid billing.'
    )
    collection_point_ids = fields.Many2many(
        'wm.collection.point',
        string='Collection Sites',
        domain="[('partner_id', '=', partner_id)]",
        help='Select the sites to include in this contract. '
             'Only sites belonging to the selected customer are shown.',
    )

    # ------------------------------------------------------------------
    # Default values computation
    # ------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        """
        Pre-fill wizard defaults from context, order, or confirmed quotation.
        """
        defaults = super().default_get(fields_list)
        order_id = defaults.get('order_id') or self.env.context.get('default_order_id')
        lead_id = defaults.get('lead_id') or self.env.context.get('default_lead_id')

        if order_id:
            order = self.env['sale.order'].browse(order_id)
            if 'partner_id' in fields_list and not defaults.get('partner_id'):
                defaults['partner_id'] = order.partner_id.id
            if 'fixed_price' in fields_list:
                defaults['fixed_price'] = order.amount_total
            if order.opportunity_id:
                if 'lead_id' in fields_list and not defaults.get('lead_id'):
                    defaults['lead_id'] = order.opportunity_id.id
                if 'service_type' in fields_list and not defaults.get('service_type'):
                    defaults['service_type'] = order.opportunity_id.wm_service_type or 'collection'
                if 'frequency' in fields_list and not defaults.get('frequency'):
                    defaults['frequency'] = order.opportunity_id.wm_frequency or 'weekly'
        elif lead_id:
            lead = self.env['crm.lead'].browse(lead_id)
            quotation = lead.order_ids.filtered(lambda o: o.state == 'sale')[:1]
            if quotation and 'fixed_price' in fields_list:
                defaults['fixed_price'] = quotation.amount_total
        return defaults

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @api.constrains('contract_from_date', 'contract_to_date')
    def _check_dates(self):
        """
        Validate that the proposed contract start date precedes the end date
        and that the contract period meets the minimum duration configured in
        system settings.
        """
        for wiz in self:
            if wiz.contract_to_date and wiz.contract_from_date:
                if wiz.contract_to_date < wiz.contract_from_date:
                    raise ValidationError(
                        _('Contract End Date cannot be before Start Date.')
                    )

    # ------------------------------------------------------------------
    # Confirmation action
    # ------------------------------------------------------------------
    def action_confirm_conversion(self):
        """
        Create the wm.partner.contract from the wizard values.
        """
        self.ensure_one()

        # Auto-create collection point if customer has none selected
        target_sites = self.collection_point_ids
        if not target_sites:
            existing_site = self.env['wm.collection.point'].search([
                ('partner_id', '=', self.partner_id.id)
            ], limit=1)
            if existing_site:
                target_sites = existing_site
            else:
                target_sites = self.env['wm.collection.point'].create({
                    'name': f"{self.partner_id.name} - Main Site",
                    'partner_id': self.partner_id.id,
                    'street': self.partner_id.street,
                    'city': self.partner_id.city,
                    'state_id': self.partner_id.state_id.id if self.partner_id.state_id else False,
                    'zip': self.partner_id.zip,
                    'country_id': self.partner_id.country_id.id if self.partner_id.country_id else False,
                })

        contract_line_vals = []
        if self.lead_id and self.lead_id.lead_line_ids:
            for line in self.lead_id.lead_line_ids:
                contract_line_vals.append(fields.Command.create({
                    'category_id': line.category_id.id,
                    'product_ids': [fields.Command.set(line.product_ids.ids)] if line.product_ids else False,
                    'price': line.price_unit,
                }))

        contract_vals = {
            'partner_id': self.partner_id.id,
            'crm_lead_id': self.lead_id.id if self.lead_id else False,
            'sale_order_id': self.order_id.id if self.order_id else False,
            'from_date': self.contract_from_date,
            'to_date': self.contract_to_date,
            'frequency': self.frequency,
            'no_of_frequency': self.no_of_frequency,
            'billing_basis': self.billing_basis,
            'sla_id': self.sla_id.id,
            'state': 'draft',
            'fixed_price': self.fixed_price if self.billing_basis in ('per_collection', 'hybrid') else 0.0,
            'max_weight': self.max_weight if self.billing_basis == 'per_collection' else 0.0,
            'overweight_price': self.overweight_price if self.billing_basis == 'per_collection' else 0.0,
            'included_weight': self.included_weight if self.billing_basis == 'hybrid' else 0.0,
            'collection_point_ids': [fields.Command.set(target_sites.ids)],
        }
        if contract_line_vals:
            contract_vals['contract_line_ids'] = contract_line_vals

        contract = self.env['wm.partner.contract'].create(contract_vals)

        # Post chatter notes linking to the new contract
        if self.lead_id:
            self.lead_id.message_post(
                body=_(
                    'Converted to contract <a href="/web#id=%(id)s&model=wm.partner.contract">%(name)s</a>.',
                    id=contract.id,
                    name=contract.name,
                )
            )
            # Mark pending contract-creation activities on the lead as done
            todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if todo_activity_type:
                summary_prefix = _('Quotation accepted')
                activities = self.lead_id.activity_ids.filtered(
                    lambda a: a.activity_type_id == todo_activity_type
                    and summary_prefix in (a.summary or '')
                )
                if activities:
                    activities.action_feedback(feedback=_('Contract created: %s') % contract.name)

        if self.order_id:
            self.order_id.message_post(
                body=_(
                    'Contract <a href="/web#id=%(id)s&model=wm.partner.contract">%(name)s</a> created from this quotation.',
                    id=contract.id,
                    name=contract.name,
                )
            )

        # Open the new contract form so the user can complete it
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Contract'),
            'res_model': 'wm.partner.contract',
            'view_mode': 'form',
            'res_id': contract.id,
            'target': 'current',
        }
