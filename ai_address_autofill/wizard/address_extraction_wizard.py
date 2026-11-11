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
from odoo.exceptions import UserError

COUNTRY_ALIASES = {
    'usa': 'US',
    'u.s.a.': 'US',
    'u.s.': 'US',
    'united states of america': 'US',
    'uk': 'GB',
    'u.k.': 'GB',
    'united kingdom': 'GB',
    'great britain': 'GB',
    'uae': 'AE',
    'u.a.e.': 'AE',
    'united arab emirates': 'AE',
}


class AddressExtractionWizard(models.TransientModel):
    _name = 'address.extraction.wizard'
    _description = 'AI Address Extraction Wizard'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Target Contact",
        help="Select the contact to update.",
    )
    raw_address = fields.Text(
        string="Full Address Text",
        required=True,
        help="Enter or paste the unstructured address string here.",
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Input Address'),
            ('extracted', 'Review & Confirm'),
        ],
        string="Status",
        default='draft',
        required=True,
    )

    is_partner_readonly = fields.Boolean(
        default=False,
        help="Technical flag indicating if the target contact should be readonly.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('partner_readonly') or self.env.context.get('default_is_partner_readonly'):
            res['is_partner_readonly'] = True
        partner_id = res.get('partner_id') or self.env.context.get('default_partner_id')
        if not partner_id and self.env.context.get('active_model') == 'res.partner' and self.env.context.get('active_id'):
            partner_id = self.env.context.get('active_id')
            res['partner_id'] = partner_id
        if partner_id and not res.get('raw_address'):
            partner = self.env['res.partner'].browse(partner_id)
            address_parts = [
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name if partner.state_id else False,
                partner.zip,
                partner.country_id.name if partner.country_id else False,
            ]
            non_empty_parts = [p.strip() for p in address_parts if p and p.strip()]
            if non_empty_parts:
                res['raw_address'] = ", ".join(non_empty_parts)
        return res

    extracted_street = fields.Char(
        string="Street Address",
    )
    extracted_street2 = fields.Char(
        string="Street 2",
    )
    extracted_city = fields.Char(
        string="City",
    )
    extracted_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string="State / Province",
        domain="[('country_id', '=?', extracted_country_id)]",
    )
    extracted_zip = fields.Char(
        string="ZIP / Postal Code",
    )
    extracted_country_id = fields.Many2one(
        comodel_name='res.country',
        string="Country",
    )
    overwrite_existing = fields.Boolean(
        string="Overwrite Existing Address",
        default=False,
        help="When enabled, replaces existing address fields on the contact.",
    )

    def action_extract_address(self):
        """Send address text to Gemini service and resolve components into Odoo records."""
        self.ensure_one()
        if not self.raw_address or not self.raw_address.strip():
            raise UserError(self.env._("Please enter an address in the text area."))

        extracted = self.env['gemini.service'].extract_address(self.raw_address)

        raw_country = extracted.get('country') or ''
        raw_state = extracted.get('state') or ''

        country_record = self._resolve_country(raw_country)
        state_record = self._resolve_state(raw_state, country_record)

        if not country_record and state_record and state_record.country_id:
            country_record = state_record.country_id

        self.write({
            'state': 'extracted',
            'extracted_street': extracted.get('street') or False,
            'extracted_street2': extracted.get('street2') or False,
            'extracted_city': extracted.get('city') or False,
            'extracted_zip': extracted.get('zip') or False,
            'extracted_country_id': country_record.id if country_record else False,
            'extracted_state_id': state_record.id if state_record else False,
        })

        return {
            'name': self.env._('AI Address Autofill'),
            'type': 'ir.actions.act_window',
            'res_model': 'address.extraction.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _resolve_country(self, raw_country):
        """Match country string against existing res.country records."""
        if not raw_country or not raw_country.strip():
            return self.env['res.country']

        query = raw_country.strip()
        country_model = self.env['res.country']

        code_alias = COUNTRY_ALIASES.get(query.lower())
        if code_alias:
            country = country_model.search([('code', '=ilike', code_alias)], limit=1)
            if country:
                return country

        country = country_model.search([('code', '=ilike', query)], limit=1)
        if country:
            return country

        country = country_model.search([('name', '=ilike', query)], limit=1)
        if country:
            return country

        country = country_model.search([('name', 'ilike', query)], limit=1)
        if country:
            return country

        return self.env['res.country']

    def _resolve_state(self, raw_state, country_record):
        """Match state string against res.country.state."""
        if not raw_state or not raw_state.strip():
            return self.env['res.country.state']

        query = raw_state.strip()
        state_model = self.env['res.country.state']

        if country_record:
            state = state_model.search([
                ('country_id', '=', country_record.id),
                '|', ('code', '=ilike', query), ('name', '=ilike', query),
            ], limit=1)
            if state:
                return state

            state = state_model.search([
                ('country_id', '=', country_record.id),
                ('name', 'ilike', query),
            ], limit=1)
            if state:
                return state

        state = state_model.search([
            '|', ('code', '=ilike', query), ('name', '=ilike', query),
        ], limit=1)
        if state:
            return state

        return self.env['res.country.state']

    def action_apply_to_contact(self):
        """Apply confirmed address values to the selected partner."""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(self.env._("Please select a target contact to update, or click 'Create New Contact' instead."))

        partner = self.partner_id
        update_vals = {}

        if self.overwrite_existing:
            if self.extracted_street:
                update_vals['street'] = self.extracted_street
            if self.extracted_street2:
                update_vals['street2'] = self.extracted_street2
            if self.extracted_city:
                update_vals['city'] = self.extracted_city
            if self.extracted_state_id:
                update_vals['state_id'] = self.extracted_state_id.id
            if self.extracted_zip:
                update_vals['zip'] = self.extracted_zip
            if self.extracted_country_id:
                update_vals['country_id'] = self.extracted_country_id.id
        else:
            if self.extracted_street and not partner.street:
                update_vals['street'] = self.extracted_street
            if self.extracted_street2 and not partner.street2:
                update_vals['street2'] = self.extracted_street2
            if self.extracted_city and not partner.city:
                update_vals['city'] = self.extracted_city
            if self.extracted_state_id and not partner.state_id:
                update_vals['state_id'] = self.extracted_state_id.id
            if self.extracted_zip and not partner.zip:
                update_vals['zip'] = self.extracted_zip
            if self.extracted_country_id and not partner.country_id:
                update_vals['country_id'] = self.extracted_country_id.id

        if update_vals:
            partner.write(update_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Contact Updated'),
                'message': self.env._("Address successfully applied to '%s'.", partner.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_create_contact(self):
        """Create a new contact using the confirmed address components."""
        self.ensure_one()
        name = (self.raw_address.splitlines()[0][:50] if self.raw_address else False) or self.env._("New Contact")

        partner_vals = {
            'name': name,
            'street': self.extracted_street or False,
            'street2': self.extracted_street2 or False,
            'city': self.extracted_city or False,
            'state_id': self.extracted_state_id.id if self.extracted_state_id else False,
            'zip': self.extracted_zip or False,
            'country_id': self.extracted_country_id.id if self.extracted_country_id else False,
        }

        new_partner = self.env['res.partner'].create(partner_vals)

        return {
            'name': self.env._('New Contact'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': new_partner.id,
            'view_mode': 'form',
            'target': 'current',
        }
