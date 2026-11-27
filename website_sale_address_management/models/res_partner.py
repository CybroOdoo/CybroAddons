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
from odoo import models

MANAGED_FIELDS = ('phone', 'street', 'city', 'zip')


class ResPartner(models.Model):
    """Apply configured billing and delivery mandatory address field rules."""

    _inherit = 'res.partner'

    def _get_mandatory_billing_address_fields(self, country_sudo, **kwargs):
        """Return mandatory billing address field names per module configuration."""
        mandatory = super()._get_mandatory_billing_address_fields(
            country_sudo, **kwargs)
        config = self.env['res.config.settings'].sudo().get_address_field_config('billing')
        for fname in MANAGED_FIELDS:
            if config[fname]['required']:
                mandatory.add(fname)
            else:
                mandatory.discard(fname)
        return mandatory

    def _get_mandatory_delivery_address_fields(self, country_sudo, **kwargs):
        """Return mandatory delivery address field names per module configuration."""
        mandatory = super()._get_mandatory_delivery_address_fields(
            country_sudo, **kwargs)
        config = self.env['res.config.settings'].sudo().get_address_field_config('delivery')
        for fname in MANAGED_FIELDS:
            if config[fname]['required']:
                mandatory.add(fname)
            else:
                mandatory.discard(fname)
        return mandatory
