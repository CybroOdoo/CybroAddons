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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    show_address_autofill_button = fields.Boolean(
        compute='_compute_show_address_autofill_button',
        default=True,
    )

    @api.model
    def _is_address_extraction_enabled(self):
        """Check if address autofill is enabled in settings."""
        val = self.env['gemini.service']._get_param_value('ai_address_autofill.address_autofill', default=None)
        if val is None:
            # Fallback to older config keys if present
            for old_key in (
                'ai_address_autofill.enable_address_extraction',
                'ai_address_autofill.extract_from_form_view',
                'ai_address_autofill.extract_from_list_view',
            ):
                val = self.env['gemini.service']._get_param_value(old_key, default=None)
                if val is not None:
                    break
        if val is None:
            val = 'True'
        return str(val).lower() in ('true', '1', 't')

    def _compute_show_address_autofill_button(self):
        is_enabled = self._is_address_extraction_enabled()
        for record in self:
            record.show_address_autofill_button = is_enabled

    @api.model
    def check_address_extraction_list_enabled(self):
        """Check if extraction is enabled in settings."""
        return self._is_address_extraction_enabled()

    def action_open_address_extractor(self):
        """Open the AI Address Extraction wizard for this contact record."""
        if not self._is_address_extraction_enabled():
            raise UserError(self.env._("Address extraction is disabled in settings."))

        partner = self[:1]
        context = {
            'active_model': 'res.partner',
        }
        if partner:
            context.update({
                'default_partner_id': partner.id,
                'default_is_partner_readonly': True,
                'partner_readonly': True,
                'active_id': partner.id,
            })
            # Prepopulate with existing formatted address if available
            address_parts = [
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name if partner.state_id else False,
                partner.zip,
                partner.country_id.name if partner.country_id else False,
            ]
            non_empty_parts = [part.strip() for part in address_parts if part and part.strip()]
            if non_empty_parts:
                context['default_raw_address'] = ", ".join(non_empty_parts)

        return {
            'name': self.env._('Address Autofill'),
            'type': 'ir.actions.act_window',
            'res_model': 'address.extraction.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
