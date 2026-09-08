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
from odoo.exceptions import UserError


class CrmLeadWM(models.Model):
    """Extends CRM Lead with waste management qualification and contract conversion workflows."""
    _inherit = 'crm.lead'

    # ------------------------------------------------------------------
    # Waste-qualification fields (all optional)
    # ------------------------------------------------------------------
    wm_service_type = fields.Selection([
        ('collection', 'Waste Collection'),
        ('recycling', 'Recycling Services'),
        ('both', 'Collection + Recycling'),
        ('hazardous', 'Hazardous Waste Handling'),
        ('other', 'Other'),
    ], string='Service Type', default='collection')

    wm_estimated_weight_kg = fields.Float(
        string='Est. Monthly Weight (kg)',
        help='Estimated total waste weight per month across all sites.'
    )
    wm_no_of_sites = fields.Integer(
        string='Number of Sites',
        help='Number of collection points / sites to be covered.'
    )
    wm_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Collection Frequency')

    wm_has_hazardous = fields.Boolean(
        string='Includes Hazardous Waste',
        default=False,
    )
    wm_special_requirements = fields.Text(
        string='Special Requirements',
        help='Any site access restrictions, special handling needs, regulatory notes.',
    )
    lead_line_ids = fields.One2many(
        'crm.lead.line',
        'lead_id',
        string='Quoted Waste Categories',
    )

    # ------------------------------------------------------------------
    # Dynamic Expected Revenue Computation from Quoted Lines
    # ------------------------------------------------------------------
    @api.onchange('lead_line_ids')
    def _onchange_lead_line_ids(self):
        """
        Update estimated monthly weight and expected revenue when lead lines
        change.
        """
        if self.lead_line_ids:
            total_weight = sum(self.lead_line_ids.mapped('estimated_weight_kg'))
            if total_weight > 0:
                self.wm_estimated_weight_kg = total_weight
            lines_subtotal = sum(self.lead_line_ids.mapped('subtotal'))
            if lines_subtotal > 0:
                self.expected_revenue = lines_subtotal

    # ------------------------------------------------------------------
    # Traceability: contracts originated from this lead
    # ------------------------------------------------------------------
    wm_contract_ids = fields.One2many(
        'wm.partner.contract',
        'crm_lead_id',
        string='Waste Contracts',
        readonly=True,
    )
    wm_contract_count = fields.Integer(
        string='Contracts',
        compute='_compute_wm_contract_count',
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends('wm_contract_ids')
    def _compute_wm_contract_count(self):
        """
        Count contracts linked to this lead for the smart button badge.
        """
        for lead in self:
            lead.wm_contract_count = len(lead.wm_contract_ids)

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------
    def action_create_quotation(self):
        """
        Create a draft Sales quotation from this Won opportunity's
        waste category lines. Replaces the direct-to-contract flow —
        the contract is now created after the quotation is accepted,
        not immediately on Won.
        """
        self.ensure_one()

        if self.won_status != 'won':
            raise UserError(_(
                'Only Won opportunities can generate a quotation. '
                'Move this opportunity to a Won stage first.'
            ))
        if not self.partner_id:
            raise UserError(_(
                'Please assign a Customer before creating a quotation.'
            ))
        if not self.lead_line_ids:
            raise UserError(_(
                'Add at least one waste category line before creating a quotation.'
            ))

        order_lines = []
        for line in self.lead_line_ids:
            product = line.product_ids[:1] or line.category_id.service_product_id
            if not product:
                product = self.env['product.product'].search([
                    ('wm_waste_category_id', '=', line.category_id.id)
                ], limit=1)
            if not product:
                product = self.env['product.product'].search([
                    ('name', '=', f"{line.category_id.name} Service"),
                    ('type', '=', 'service'),
                ], limit=1)
            if not product:
                product = self.env['product.product'].sudo().create({
                    'name': f"{line.category_id.name} Service",
                    'type': 'service',
                    'wm_waste_category_id': line.category_id.id,
                })
            if not line.category_id.service_product_id:
                line.category_id.sudo().service_product_id = product.id

            order_lines.append(fields.Command.create({
                'product_id': product.id,
                'name': f"{line.category_id.name} — est. {line.estimated_weight_kg} kg/month",
                'product_uom_qty': line.estimated_weight_kg,
                'price_unit': line.price_unit,
            }))

        quotation = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'opportunity_id': self.id,
            'order_line': order_lines,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotations'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': quotation.id,
            'target': 'current',
        }

    def action_convert_to_wm_contract(self):
        """
        Convert a won CRM opportunity into a waste management service contract,
        transferring lead line details to contract categories and pricing
        configurations.
        """
        self.ensure_one()

        # Guard 1: must be in Won stage
        if self.won_status != 'won':
            raise UserError(_(
                'Only Won opportunities can be converted to a waste management '
                'contract. Move this opportunity to a Won stage first.'
            ))

        # Guard 2: a customer must be assigned
        if not self.partner_id:
            raise UserError(_(
                'Please assign a Customer to this opportunity before '
                'converting to a contract.'
            ))

        # Guard 3 (non-blocking): check for existing active contracts so the
        # wizard can surface a warning banner. We look for sent/signed/
        # confirmed/ongoing — draft contracts do NOT count here.
        existing = self.env['wm.partner.contract'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ('sent', 'signed', 'confirmed', 'ongoing')),
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Convert to Waste Management Contract'),
            'res_model': 'wm.lead.conversion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_frequency': self.wm_frequency or 'weekly',
                'default_service_type': self.wm_service_type,
                'default_has_existing_contract': bool(existing),
                'default_existing_contract_name': existing.name if existing else '',
            },
        }

    def action_view_wm_contracts(self):
        """
        Smart button action: view all contracts linked to this lead.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'res_model': 'wm.partner.contract',
            'view_mode': 'list,form',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }
