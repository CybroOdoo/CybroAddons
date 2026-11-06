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

# Characters removed from the generated SEO content
SEO_STRIP_TABLE = str.maketrans('', '', "<>(),'/")


class GenerateSeo(models.Model):
    """In this model user can generate SEO
    based on product or product category"""
    _name = 'seo.generate'
    _description = 'Generate SEO'
    _rec_name = 'model_name'

    model_name = fields.Selection(
        [('product', 'Product'),
         ('product_category', 'Product Category')],
        string='SEO Meta Configuration For',
        required=True, help='Select the model to generate the SEO for')
    meta_title_ids = fields.Many2many(
        'website.seo.attributes', 'seo_generate_meta_title_rel',
        'seo_generate_id', 'attribute_id',
        required=True, help='Choose the meta title attributes')
    meta_description_ids = fields.Many2many(
        'website.seo.attributes', 'seo_generate_meta_description_rel',
        'seo_generate_id', 'attribute_id',
        required=True, help='Choose the meta description attributes')
    attribute_separator = fields.Char(
        string="Multi Attribute Separator", default="|", required=True,
        help='Separator placed between multiple attributes')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company, help='Choose the company')
    meta_ids = fields.Many2many(
        'website.seo.attributes', 'seo_generate_meta_rel',
        'seo_generate_id', 'attribute_id', string='Available Attributes',
        help='Attributes available for the selected model')
    state = fields.Selection(
        [('activated', 'Activated'), ('deactivated', 'Deactivated')],
        string='Status', default='deactivated', help='Status of the record')

    @api.onchange('model_name')
    def _onchange_model_name(self):
        """Configure meta ids when the model is changed"""
        self.meta_title_ids = False
        self.meta_description_ids = False
        if self.model_name:
            self.meta_ids = self.env['website.seo.attributes'].search(
                [('models', '=', self.model_name)])

    def _get_attribute_fields(self, attributes, attribute_field):
        """Return the unique field names selected on the attributes.

        :param attributes: recordset of website.seo.attributes
        :param str attribute_field: 'product' or 'category'
        :return: list of field names, keeping the selection order
        """
        return list(dict.fromkeys(
            name for name in attributes.mapped(attribute_field) if name))

    def _compose_seo_value(self, values, field_names):
        """Join the field values of a record into a single SEO string."""
        parts = []
        for name in field_names:
            value = values.get(name)
            if not value:
                continue
            if isinstance(value, (tuple, list)):
                # Many2one values are returned as (id, display_name)
                value = value[1]
            parts.append(str(value))
        return self.attribute_separator.join(parts).translate(
            SEO_STRIP_TABLE)

    def _generate_seo(self, model, domain, attribute_field):
        """Write the meta title, keywords and description on the records.

        :param str model: technical name of the model to update
        :param list domain: domain selecting the records to update
        :param str attribute_field: field of website.seo.attributes
            holding the name of the field to read ('product'/'category')
        """
        title_fields = self._get_attribute_fields(
            self.meta_title_ids, attribute_field)
        description_fields = self._get_attribute_fields(
            self.meta_description_ids, attribute_field)
        if not title_fields and not description_fields:
            return
        read_fields = list(dict.fromkeys(
            title_fields + description_fields + ['name']))
        records = self.env[model]
        for values in records.search_read(domain, fields=read_fields):
            vals = {}
            if title_fields:
                vals['website_meta_title'] = self._compose_seo_value(
                    values, title_fields)
                vals['website_meta_keywords'] = values['name']
            if description_fields:
                vals['website_meta_description'] = self._compose_seo_value(
                    values, description_fields)
            records.browse(values['id']).write(vals)

    def action_save_seo_info(self):
        """Save the SEO content"""
        self.ensure_one()
        self.state = 'activated'
        self.search([('id', '!=', self.id)]).write({'state': 'deactivated'})
        if self.model_name == 'product':
            self._generate_seo('product.template', [], 'product')
            message = self.env._("Successfully generated the SEO for all "
                                 "products.")
        elif self.model_name == 'product_category':
            self._generate_seo('product.public.category',
                               [('is_auto_seo', '=', True)], 'category')
            message = self.env._("Successfully generated the SEO only for "
                                 "product categories with auto SEO enabled.")
        else:
            return False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_deactivate_seo(self):
        """Deactivate the SEO when the Archive button is clicked"""
        self.state = 'deactivated'
