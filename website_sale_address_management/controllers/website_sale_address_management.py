# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

MANAGED_FIELDS = ('phone', 'street', 'city', 'zip')


class CustomWebsiteSale(WebsiteSale):
    """Adapt the website sale address form to the module configuration."""

    @staticmethod
    def _get_address_config(address_type):
        """Return the configured visibility/required flags of an address."""
        return request.env['res.config.settings'].sudo(
        ).get_address_field_config(address_type)

    def _apply_address_config(self, fields_set, address_type):
        """Adapt a set of mandatory fields to the module configuration:
        fields that are not configured as required are dropped and the ones
        configured as required (and visible) are added."""
        config = self._get_address_config(address_type)
        for fname in MANAGED_FIELDS:
            if config[fname]['required']:
                fields_set.add(fname)
            else:
                fields_set.discard(fname)
        return fields_set

    def _get_mandatory_delivery_address_fields(self, country_sudo):
        """Return the mandatory fields of a delivery address."""
        mandatory_fields = set(
            super()._get_mandatory_delivery_address_fields(country_sudo))
        return self._apply_address_config(mandatory_fields, 'delivery')

    def _get_mandatory_billing_address_fields(self, country_sudo):
        """Return the mandatory fields of a billing address."""
        mandatory_fields = set(
            super()._get_mandatory_billing_address_fields(country_sudo))
        return self._apply_address_config(mandatory_fields, 'billing')

    def _prepare_address_form_values(self, *args, address_type='billing',
                                     **kwargs):
        """Preselect the configured default country of a new address."""
        rendering_values = super()._prepare_address_form_values(
            *args, address_type=address_type, **kwargs)
        if (
            not kwargs.get('order_sudo')
            or rendering_values.get('partner_sudo')
            or rendering_values.get('country')
        ):
            return rendering_values
        country_id = self._get_address_config(
            address_type)['default_country_id']
        country = request.env['res.country'].sudo().browse(country_id).exists()
        if country:
            address_fields = country.get_address_fields()
            rendering_values.update({
                'country': country,
                'country_states': country.state_ids,
                'zip_before_city': (
                    'zip' in address_fields and 'city' in address_fields
                    and address_fields.index('zip')
                    < address_fields.index('city')
                ),
            })
        return rendering_values

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        """Run the core validation, then ignore the missing fields that are
        not configured as required for the submitted address type(s)."""
        invalid_fields, missing_fields, error_messages = super(
        )._validate_address_values(
            address_values, partner_sudo, address_type,
            use_delivery_as_billing, required_fields, **kwargs)
        if not missing_fields:
            return invalid_fields, missing_fields, error_messages
        types = {address_type}
        if use_delivery_as_billing:
            types |= {'billing', 'delivery'}
        configs = [self._get_address_config(a_type) for a_type in types]
        optional_fields = {
            fname for fname in MANAGED_FIELDS
            if not any(config[fname]['required'] for config in configs)
        }
        missing_fields = missing_fields - optional_fields
        if not missing_fields:
            # The core validation appends its "required fields are empty"
            # message last, only when some field is missing.
            error_messages.pop()
        return invalid_fields, missing_fields, error_messages
