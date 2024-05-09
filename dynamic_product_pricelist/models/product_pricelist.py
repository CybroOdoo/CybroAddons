# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class ProductPriceList(models.Model):
    _inherit = 'product.pricelist'

    is_show_product_pricelist = fields.Boolean(
        string='Show the pricelist in product view', default=False, groups='product.group_sale_pricelist',
        help='If set then  product pricelist could be seen as a field in product and product variant')

    def check_pricelist_condition(self):
        if self.item_ids:
            for rec in self.item_ids:
                variant = False
                pricelist_name = self.name.replace(" ", "_")
                if rec.applied_on == '3_global':
                    products = self.env['product.template'].search([])
                elif rec.applied_on == '2_product_category':
                    products = self.env['product.template'].search([('categ_id', '=', rec.categ_id.id)])
                elif rec.applied_on == '0_product_variant':
                    variant = True
                    products = rec.product_id
                else:
                    products = rec.product_tmpl_id
                if variant:
                    model = 'product.product'
                    inherit_id = self.env.ref(
                        'product.product_product_tree_view')
                    model_id = self.env.ref(
                        'product.model_product_product').id
                    name = 'variant_'
                else:
                    model = 'product.template'
                    inherit_id = self.env.ref(
                        'product.product_template_tree_view')
                    model_id = self.env.ref(
                      'product.model_product_template').id
                    name = 'temp_'
                field_id = self.env['ir.model.fields'].search(
                    [('model_id', '=', model_id),
                     ('name', 'ilike', 'x_' + str(name) + str(self.id))])
                if not field_id:
                    field_id = self.env['ir.model.fields'].sudo().create({
                        'name': 'x_' + str(name) + str(self.id) + pricelist_name,
                        'field_description': pricelist_name,
                        'model_id': model_id,
                        'ttype': 'float',
                    })
                view = self.env['ir.ui.view'].search([('name', '=', 'product.dynamic.fields.%s' % pricelist_name),
                                                      ('model', '=', model)])
                if not view:
                    arch_base = _('<?xml version="1.0"?>'
                                  '<data>'
                                  '<field name="standard_price" position="after" '
                                  'groups="dynamic_product_pricelist.group_show_sale_pricelist">'
                                  '<field name="%s" />'
                                  '</field>'
                                  '</data>') % (
                                        'x_' + str(name) + str(self.id) + pricelist_name)
                    self.env['ir.ui.view'].sudo().create(
                        {'name': 'product.dynamic.fields.%s' % pricelist_name,
                         'type': 'tree',
                         'model': model,
                         'mode': 'extension',
                         'inherit_id': inherit_id.id,
                         'arch_base': arch_base,
                         'active': True})
                if rec.compute_price == 'fixed':
                    products.update({
                            field_id.name: rec.fixed_price
                        })

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.is_show_product_pricelist:
            res.check_pricelist_condition()
        return res

    def write(self, vals):
        res = super().write(vals)
        if self.is_show_product_pricelist:
            self.check_pricelist_condition()
        return res

    def unlink(self):
        for res in self:
            for rec in res.item_ids:
                if rec.applied_on == '0_product_variant':
                    name = 'variant_'
                    model = 'product.product'
                    inherit_id = self.env.ref(
                        'product.product_product_tree_view')
                    model_id = self.env.ref(
                        'product.model_product_product').id
                else:
                    name = 'temp_'
                    model = 'product.template'
                    inherit_id = self.env.ref(
                        'product.product_template_tree_view')
                    model_id = self.env.ref(
                        'product.model_product_template').id
                pricelist_name = res.name.replace(" ", "_")
                views = self.env['ir.ui.view'].search(
                    [(
                     'name', '=', 'product.dynamic.fields.%s' % pricelist_name),
                     ('type', '=', 'tree'),
                     ('model', '=', model),
                     ('inherit_id', '=', inherit_id.id)])
                for view in views:
                    view.active = False
                self.env['ir.model.fields'].search(
                    [('model_id', '=', model_id),
                     ('name', '=', 'x_' + str(name) + str(
                         res.id) + pricelist_name)]).unlink()
        return super().unlink()
