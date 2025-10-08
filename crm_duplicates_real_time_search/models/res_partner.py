# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Dhanya B(<https://www.cybrosys.com>)
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
import ast
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_duplicate_contact = fields.Boolean(String='Is Duplicate',
                                          help='Enable this to show the '
                                               'duplicate leads')

    def _get_partner_fields(self, param_key):
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            param_key)
        return ast.literal_eval(param_value) if param_value else []

    def _check_duplicates(self, vals, fields_list, model, strict=False):
        for field_id in fields_list:
            contact_field = self.env['ir.model.fields'].browse(field_id)
            field_name = contact_field.name
            if vals.get(field_name):
                domain = [(field_name, '=', vals.get(field_name))]
                if not strict:
                    domain.append(('id', '!=', self.id))
                existing_partner = self.env[model].search(domain, limit=1)
                if existing_partner:
                    if strict:
                        raise ValidationError(
                            _("The %s is already used for contact %s.") %
                            (contact_field.field_description,
                             existing_partner.name)
                        )
                    return True
        return False

    @api.model
    def create(self, vals):
        partner_fields_rigid = self._get_partner_fields(
            'crm_duplicates_real_time_search.partner_fields_rigid_ids')
        partner_fields_soft = self._get_partner_fields(
            'crm_duplicates_real_time_search.partner_fields_soft_ids')
        self._check_duplicates(vals, partner_fields_rigid, 'res.partner',
                               strict=True)
        flag = self._check_duplicates(vals, partner_fields_soft, 'res.partner')
        res = super(ResPartner, self).create(vals)
        if flag:
            res.write({'is_duplicate_contact': True})
            res.message_post(body=_('created duplicate values.'))
        return res

    def write(self, vals):
        partner_fields_rigid = self._get_partner_fields(
            'crm_duplicates_real_time_search.partner_fields_rigid_ids')
        partner_fields_soft = self._get_partner_fields(
            'crm_duplicates_real_time_search.partner_fields_soft_ids')
        self._check_duplicates(vals, partner_fields_rigid, 'res.partner',
                               strict=True)
        flag = self._check_duplicates(vals, partner_fields_soft, 'res.partner')
        res = super(ResPartner, self).write(vals)
        if flag:
            self.write({'is_duplicate_contact': True})
            self.message_post(body=_('Created duplicate values.'))
        return res
