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


class CRMLead(models.Model):
    """
    Extend CRM Lead Model to handle duplicate values.
    """
    _inherit = 'crm.lead'

    is_duplicate_lead = fields.Boolean(String='Is Duplicate',
                                       help='Enable this to show the duplicate'
                                            ' leads')

    def _get_crm_fields(self, param_key):
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            param_key)
        return ast.literal_eval(param_value) if param_value else []

    def _check_duplicate_fields(self, vals, fields_list, strict=False):
        for field in fields_list:
            crm_field = self.env['ir.model.fields'].browse(field)
            field_name = crm_field.name
            if field_name in vals:
                lead = self.env['crm.lead'].search(
                    [(field_name, '=', vals[field_name])], limit=1)
                if lead:
                    if strict:
                        raise ValidationError(
                            _("The %s is already used for opportunity %s.") % (
                                crm_field.field_description, lead.name))
                    else:
                        return crm_field.field_description
        return None

    @api.model
    def create(self, vals):
        crm_fields_rigid = self._get_crm_fields(
            'crm_duplicates_real_time_search.crm_fields_rigid_ids')
        crm_fields_soft = self._get_crm_fields(
            'crm_duplicates_real_time_search.crm_fields_soft_ids')
        duplicate_field = self._check_duplicate_fields(vals, crm_fields_rigid,
                                                       strict=True)
        if not duplicate_field:
            duplicate_field = self._check_duplicate_fields(vals,
                                                           crm_fields_soft)
        res = super(CRMLead, self).create(vals)
        if duplicate_field:
            res.write({'is_duplicate_lead': True})
            res.message_post(
                body=_('created duplicate values for %s.') % duplicate_field)

        return res

    def write(self, vals):
        crm_fields_rigid = self._get_crm_fields(
            'crm_duplicates_real_time_search.crm_fields_rigid_ids')
        crm_fields_soft = self._get_crm_fields(
            'crm_duplicates_real_time_search.crm_fields_soft_ids')
        duplicate_field = self._check_duplicate_fields(vals, crm_fields_rigid,
                                                       strict=True)
        if not duplicate_field:
            duplicate_field = self._check_duplicate_fields(vals,
                                                           crm_fields_soft)
        res = super(CRMLead, self).write(vals)
        if duplicate_field:
            self.write({'is_duplicate_lead': True})
            self.message_post(
                body=_('created duplicate values for %s.') % duplicate_field)
        return res
