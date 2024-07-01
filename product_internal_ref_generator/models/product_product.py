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


class ProductProduct(models.Model):
    """Class for products to generate the internal reference"""
    _inherit = 'product.product'

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
                for rec in res:
                    default_code = ''
                    if rec.detailed_type == 'consu':
                        default_code += 'Consu:'
                    elif rec.detailed_type == 'service':
                        default_code += 'Servi:'
                    elif rec.detailed_type == 'product':
                        default_code += 'Stora:'
                    if product_name_config:
                        if rec.name:
                            default_code += rec.name[:int(pro_name_digit)]
                            default_code += pro_name_separator
                    if pro_categ_config:
                        if rec.categ_id.name:
                            default_code += rec.categ_id.name[:int(pro_categ_digit)]
                            default_code += pro_categ_separator
                    sequence_code = 'product.sequence.ref'
                    default_code += self.env['ir.sequence'].next_by_code(
                        sequence_code)
                    rec.default_code = default_code
        return res

    @api.model
    def action_generate_internal_ref_pro(self):
        """creating the internal reference"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.product'].browse(active_ids)
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
                    if rec.name:
                        default_code += rec.name[:int(pro_name_digit)]
                        default_code += pro_name_separator
                if pro_categ_config:
                    if rec.categ_id.name:
                        default_code += rec.categ_id.name[:int(pro_categ_digit)]
                        default_code += pro_categ_separator
                sequence_code = 'product.sequence.ref'
                default_code += self.env['ir.sequence'].next_by_code(
                    sequence_code)
                rec.default_code = default_code
        return self
