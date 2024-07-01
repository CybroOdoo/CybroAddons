# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    """Class for product template to generate internal reference"""
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """supering the create function, generating the internal reference"""
        res = super().create(vals_list)
        if 'default_code' in vals_list:
            pass
        else:
            auto_generate_internal_ref = self.env['ir.config_parameter'].sudo().get_param(
                'product_internal_ref_generator.auto_generate_internal_ref')
            if auto_generate_internal_ref:
                product_name_config = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.product_name_config')
                pro_name_digit = self.env['ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_name_digit')
                pro_name_separator = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_name_separator')
                pro_categ_config = self.env['ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_categ_config')
                pro_categ_digit = self.env['ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_categ_digit')
                pro_categ_separator = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_categ_separator')
                pro_template_config = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_template_config')
                pro_template_digit = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_template_digit')
                pro_template_separator = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'product_internal_ref_generator.pro_template_separator')
                for rec in res:
                    default_code = ''
                    if rec.detailed_type == 'consu':
                        default_code += 'Consu:'
                    elif rec.detailed_type == 'service':
                        default_code += 'Servi:'
                    elif rec.detailed_type == 'product':
                        default_code += 'Stora:'
                    if product_name_config:
                        default_code += rec.name[:int(pro_name_digit)]
                        default_code += pro_name_separator
                    if pro_categ_config:
                        default_code += rec.categ_id.name[:int(pro_categ_digit)]
                        default_code += pro_categ_separator
                    if pro_template_config:
                        for attribute in rec.attribute_line_ids:
                            for value in attribute.value_ids:
                                default_code += value.name[:int(pro_template_digit)]
                                default_code += pro_template_separator
                    sequence_code = 'attribute.sequence.ref'
                    default_code += self.env['ir.sequence'].next_by_code(
                        sequence_code)
                    rec.default_code = default_code
        return res

    @api.model
    def action_generate_internal_ref(self):
        """Creating internal reference"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        product_name_config = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.product_name_config')
        pro_name_digit = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_name_digit')
        pro_name_separator = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_name_separator')
        pro_categ_config = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_categ_config')
        pro_categ_digit = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_categ_digit')
        pro_categ_separator = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_categ_separator')
        pro_template_config = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_template_config')
        pro_template_digit = self.env['ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_template_digit')
        pro_template_separator = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_internal_ref_generator.pro_template_separator')
        for rec in products:
            if not rec.default_code:
                default_code = ''
                if rec.detailed_type == 'consu':
                    default_code += 'Consu:'
                elif rec.detailed_type == 'service':
                    default_code += 'Servi:'
                elif rec.detailed_type == 'product':
                    default_code += 'Stora:'
                if product_name_config:
                    default_code += rec.name[:int(pro_name_digit)]
                    default_code += pro_name_separator
                if pro_categ_config:
                    default_code += rec.categ_id.name[:int(pro_categ_digit)]
                    default_code += pro_categ_separator
                if pro_template_config:
                    for attribute in rec.attribute_line_ids:
                        for value in attribute.value_ids:
                            default_code += value.name[:int(pro_template_digit)]
                            default_code += pro_template_separator
                sequence_code = 'attribute.sequence.ref'
                default_code += self.env['ir.sequence'].next_by_code(
                    sequence_code)
                rec.default_code = default_code
        return self
