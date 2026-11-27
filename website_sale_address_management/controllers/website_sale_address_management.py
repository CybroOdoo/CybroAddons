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

    def _prepare_address_form_values(self, *args, address_type='billing',
                                     **kwargs):
        """Preselect the configured default country of a new address."""
        rendering_values = super()._prepare_address_form_values(
            *args, address_type=address_type, **kwargs)
        partner_sudo = rendering_values.get('partner_sudo')
        if not kwargs.get('order_sudo') or (partner_sudo and partner_sudo.id):
            return rendering_values

        config = self._get_address_config(address_type)
        country_id = config.get('default_country_id')

        if country_id:
            country = request.env['res.country'].sudo().browse(country_id).exists()
            if country:
                empty_state = request.env['res.country.state']
                cities_data = (
                    country._enforce_city_choice()
                    and country._get_cities_data(empty_state.id)
                )
                extra_kwargs = {
                    k: v for k, v in kwargs.items() if k != 'use_delivery_as_billing'
                }
                use_delivery_as_billing = rendering_values.get(
                    'use_delivery_as_billing', False,
                )
                rendering_values.update({
                    'country': country,
                    'states': country.state_ids,
                    'state': empty_state,
                    'city': (
                        rendering_values['city'][:0]
                        if rendering_values.get('city')
                        else rendering_values.get('city')
                    ),
                    'cities_data': cities_data,
                    'phone_code': (
                        f'+{country.phone_code}' if country.phone_code != 0 else ''
                    ),
                    'zip_applicability': country.zip_applicability,
                    'zip_before_city': country._is_zip_before_city(),
                    'vat_label': country._get_vat_label(),
                    'required_fields': (
                        request.env['res.partner']._get_required_address_fields(
                            address_type,
                            country,
                            use_delivery_as_billing=use_delivery_as_billing,
                            **extra_kwargs,
                        )
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
