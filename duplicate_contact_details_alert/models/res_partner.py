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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import ast
import logging
import re

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def _escape_like(val):
    """Escape special characters for SQL LIKE / ILIKE patterns."""
    return val.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class ResPartner(models.Model):
    """Inherit res.partner to add validation for unique contact fields."""
    _inherit = 'res.partner'

    @api.model
    def _normalize_contact_field_value(self, field_name, value):
        """Normalize field value for duplicate detection comparison."""
        if not value:
            return ''
        if isinstance(value, str):
            value = value.strip()
            if field_name in ('phone', 'mobile') or 'phone' in field_name:
                digits = re.sub(r'\D', '', value)
                return digits if digits else value.lower()
            return value.lower()
        return str(value)

    @api.model
    def _find_duplicate_partner(self, field_name, field_value, exclude_ids=None):
        """Search for an existing partner with a matching value for field_name.

        Performs exact case-insensitive match for strings, and enhanced phone
        number matching (normalizing formatting, punctuation, and international digits).
        """
        if not field_value:
            return False

        Partner = self.env['res.partner'].sudo()
        base_domain = [('id', 'not in', exclude_ids or [])]

        clean_value = field_value.strip() if isinstance(field_value, str) else field_value

        if isinstance(clean_value, str):
            escaped_val = _escape_like(clean_value)
            partner = Partner.search(base_domain + [(field_name, '=ilike', escaped_val)], limit=1)
        else:
            partner = Partner.search(base_domain + [(field_name, '=', clean_value)], limit=1)

        if partner:
            return partner

        if isinstance(clean_value, str) and (field_name in ('phone', 'mobile') or 'phone' in field_name):
            digits = re.sub(r'\D', '', clean_value)
            if 'phone_mobile_search' in Partner._fields:
                try:
                    partner = Partner.search(base_domain + [('phone_mobile_search', '=', clean_value)], limit=1)
                    if partner:
                        return partner
                    if digits:
                        partner = Partner.search(base_domain + [('phone_mobile_search', 'like', digits)], limit=1)
                        if partner:
                            return partner
                        if len(digits) >= 7:
                            suffix_search = digits[-10:] if len(digits) >= 10 else digits[-7:]
                            partner = Partner.search(base_domain + [('phone_mobile_search', 'like', suffix_search)], limit=1)
                            if partner:
                                return partner
                except (AttributeError, KeyError, ValueError) as err:
                    _logger.debug("Error while searching partner phone: %s", err)

            if len(digits) >= 5:
                suffix = digits[-7:] if len(digits) >= 7 else digits
                phone_pattern = '%' + '%'.join(suffix) + '%'
                phone_field_names = [f for f in ('phone', 'mobile') if f in Partner._fields]
                if not phone_field_names:
                    phone_field_names = [field_name]

                search_domain = []
                for pf in phone_field_names:
                    search_domain.append((pf, '=like', phone_pattern))
                if len(search_domain) > 1:
                    search_domain = ['|'] * (len(search_domain) - 1) + search_domain

                candidates = Partner.search(base_domain + search_domain, limit=30)
                for candidate in candidates:
                    for pf in phone_field_names:
                        cand_val = candidate[pf]
                        if cand_val:
                            cand_digits = re.sub(r'\D', '', str(cand_val))
                            if cand_digits and (
                                cand_digits == digits
                                or (len(cand_digits) >= 7 and len(digits) >= 7 and
                                    (cand_digits.endswith(digits) or digits.endswith(cand_digits)))
                            ):
                                return candidate

        return False

    @api.model_create_multi
    def create(self, vals_list):
        """Check all configured fields are unique when creating contacts."""
        ICP = self.env['ir.config_parameter'].sudo()
        unique_contact_ids = ICP.get_str('duplicate_contact_details_alert.unique_contact_ids', '')
        is_unique_contact = ICP.get_bool(
            'duplicate_contact_details_alert.is_unique_contact',
            bool(unique_contact_ids),
        )
        if not is_unique_contact:
            return super().create(vals_list)

        fields_list = []
        if unique_contact_ids:
            try:
                parsed_list = ast.literal_eval(unique_contact_ids)
                if isinstance(parsed_list, (list, tuple, set)):
                    fields_list = list(parsed_list)
            except (ValueError, SyntaxError):
                fields_list = []
        if fields_list:
            contact_fields = self.env['ir.model.fields'].sudo().browse(fields_list).exists()
            duplicates = []
            seen_values = {field.name: set() for field in contact_fields}

            for vals in vals_list:
                for contact_field in contact_fields:
                    field_name = contact_field.name
                    raw_val = vals.get(field_name)
                    if not raw_val:
                        continue
                    field_value = raw_val.strip() if isinstance(raw_val, str) else raw_val
                    if not field_value:
                        continue

                    field_description = contact_field.field_description
                    norm_val = self._normalize_contact_field_value(field_name, field_value)

                    partner = self._find_duplicate_partner(field_name, field_value)
                    if partner:
                        duplicates.append((field_description, partner.name or self.env._('Unknown'), raw_val))
                    elif norm_val in seen_values[field_name]:
                        contact_name = vals.get('name') or self.env._('another contact in this batch')
                        duplicates.append((field_description, contact_name, raw_val))
                    else:
                        seen_values[field_name].add(norm_val)

            if duplicates:
                raise ValidationError(self.env._(
                    "Duplicate contact details were found:\n\n"
                    "%(details)s\n\n"
                    "Please use unique values or review the existing contacts before saving.",
                    details="\n".join(
                        f"- The {desc} '{val}' is already used for contact {p_name}."
                        for desc, p_name, val in duplicates
                    ),
                ))
        return super().create(vals_list)

    def write(self, vals):
        """Check all configured fields are unique when updating contacts."""
        ICP = self.env['ir.config_parameter'].sudo()
        unique_contact_ids = ICP.get_str('duplicate_contact_details_alert.unique_contact_ids', '')
        is_unique_contact = ICP.get_bool(
            'duplicate_contact_details_alert.is_unique_contact',
            bool(unique_contact_ids),
        )
        if not is_unique_contact:
            return super().write(vals)

        fields_list = []
        if unique_contact_ids:
            try:
                parsed_list = ast.literal_eval(unique_contact_ids)
                if isinstance(parsed_list, (list, tuple, set)):
                    fields_list = list(parsed_list)
            except (ValueError, SyntaxError):
                fields_list = []
        if fields_list:
            contact_fields = self.env['ir.model.fields'].sudo().browse(fields_list).exists()
            duplicates = []
            for contact_field in contact_fields:
                field_name = contact_field.name
                if field_name not in vals:
                    continue
                raw_val = vals.get(field_name)
                if not raw_val:
                    continue
                field_value = raw_val.strip() if isinstance(raw_val, str) else raw_val
                if not field_value:
                    continue

                field_description = contact_field.field_description
                if len(self) > 1:
                    duplicates.append((field_description, self[0].name or self.env._('Multiple Contacts'), raw_val))
                else:
                    partner = self._find_duplicate_partner(field_name, field_value, exclude_ids=self.ids)
                    if partner:
                        duplicates.append((field_description, partner.name or self.env._('Unknown'), raw_val))

            if duplicates:
                raise ValidationError(self.env._(
                    "Duplicate contact details were found:\n\n"
                    "%(details)s\n\n"
                    "Please use unique values or review the existing contacts before saving.",
                    details="\n".join(
                        f"- The {desc} '{val}' is already used for contact {p_name}."
                        for desc, p_name, val in duplicates
                    ),
                ))
        return super().write(vals)
