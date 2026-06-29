# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, _
from odoo.exceptions import ValidationError
import ast


class ResPartner(models.Model):
    """Inherit res.partner to add validation for unique contact fields."""
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        """Check all configured fields are unique when creating contacts."""
        unique_contact_ids = self.env['ir.config_parameter'].sudo().get_param(
            'duplicate_contact_details_alert.unique_contact_ids')
        partner_list = []
        fields_list = ast.literal_eval(unique_contact_ids) if unique_contact_ids else []
        for vals in vals_list:
            if fields_list:
                duplicates = []
                for x in fields_list:
                    contact_field = self.env['ir.model.fields'].browse(x)
                    field_description = contact_field.field_description
                    field_name = contact_field.name
                    if vals.get(field_name):
                        partner = self.env['res.partner'].search(
                            [(field_name, '=', vals.get(field_name))],
                            limit=1
                        )
                        if partner:
                            duplicates.append((field_description, partner, vals.get(field_name)))
                if duplicates:
                    raise ValidationError(_(
                        "Duplicate contact details were found:\n\n"
                        "%s\n\n"
                        "Please use unique values or review the existing contacts before saving."
                    ) % "\n".join(
                        f"- The {desc} '{val}' is already used for contact {p.name}."
                        for desc, p, val in duplicates
                    ))
            res = super().create(vals)
            partner_list.append(res)
        return self.browse([p.id for p in partner_list])

    def write(self, vals):
        """Check all configured fields are unique when updating contacts."""
        unique_contact_ids = self.env['ir.config_parameter'].sudo().get_param(
            'duplicate_contact_details_alert.unique_contact_ids')
        fields_list = ast.literal_eval(unique_contact_ids) if unique_contact_ids else []
        duplicates = []
        if fields_list:
            for x in fields_list:
                contact_field = self.env['ir.model.fields'].browse(x)
                field_name = contact_field.name
                field_description = contact_field.field_description
                if vals.get(field_name):
                    partner = self.env['res.partner'].search(
                        [(field_name, '=', vals.get(field_name)),
                         ('id', 'not in', self.ids)],
                        limit=1
                    )
                    if partner:
                        duplicates.append((field_description, partner, vals.get(field_name)))
            if duplicates:
                raise ValidationError(_(
                    "Duplicate contact details were found:\n\n"
                    "%s\n\n"
                    "Please use unique values or review the existing contacts before saving."
                ) % "\n".join(
                    f"- The {desc} '{val}' is already used for contact {p.name}."
                        for desc, p, val in duplicates
                ))
        return super().write(vals)
