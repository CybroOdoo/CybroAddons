from ast import literal_eval
from odoo import models
from odoo.http import request


class Website(models.Model):
    """
      Extends the 'website' model to filter product search.
    """
    _inherit = "website"
    _description = "Website"

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        """
        This method extends the base search functionality to include additional
        filtering
        """
        res = super()._search_with_fuzzy(
            search_type, search, limit, order, options)
        response = list(res)
        available_products = False
        user = request.env['res.users'].sudo().search(
            [('id', '=', request.env.user.id)])
        if response[1][0] and (response[1][0].get(
                'model', '') == 'product.template' or response[1][0].get(
                'model', '') == 'product.public.category'):
            if not user:
                mode = request.env['ir.config_parameter'].sudo().get_param(
                    'filter_mode')
                products = literal_eval(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'website_product_visibility.'
                        'available_products_for_guest_ids', 'False'))
                if mode == 'product_only':
                    available_products = request.env['product.template'].search(
                        [('id', 'in', products)])
                cat = literal_eval(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'website_product_visibility.available_cat_for_guest_ids',
                        'False'))
                available_categ = request.env['product.public.category'].search(
                    [('id', 'in', cat)])
            else:
                partner = request.env['res.partner'].sudo().search(
                    [('id', '=', user.partner_id.id)])
                mode = partner.filter_mode
                if mode == 'product_only':
                    available_products = self.available_products()
                available_categ = partner.website_available_cat_ids
            Category_avail = []
            Category = request.env['product.public.category']
            for ids in available_categ:
                if not ids.parent_id.id in available_categ.ids:
                    Category_avail.append(ids.id)
            categ = request.env['product.public.category'].search(
                [('id', 'in', Category_avail)])
            if mode == 'product_only':
                categ = Category.search([('parent_id', '=', False), (
                    'product_tmpl_ids', 'in', available_products.ids)])
            # supering shop***
            if not available_categ and not available_products and \
                    request.env.user.has_group(
                        'base.group_portal'):
                mode = request.env['ir.config_parameter'].sudo().get_param(
                    'filter_mode_portal')
                products = literal_eval(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'website_product_visibility.'
                        'available_products_for_portal_ids', 'False'))
                if mode == 'product_only':
                    available_products = request.env['product.template'].search(
                        [('id', 'in', products)])
                cat = literal_eval(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'website_product_visibility.available_cat_for_portal_ids',
                        'False'))
                available_categ = request.env['product.public.category'].search(
                    [('id', 'in', cat)])
            if available_products:
                product_category = available_products.mapped('public_categ_ids')
                category = set(response[1][0]['results'].ids).intersection(set(
                    product_category.ids))
                products = set(response[1][-1]['results'].ids).intersection(set(
                    available_products.ids))
                response[1][-1]['results'] = request.env[
                    'product.template'].browse(products)
                response[1][0]['results'] = request.env[
                    'product.public.category'].browse(category)
            if available_categ:
                categ_products = available_categ.mapped('product_tmpl_ids')
                products = set(response[1][-1]['results'].ids).intersection(set(
                    categ_products.ids))
                category = set(response[1][0]['results'].ids).intersection(set(
                    available_categ.ids))
                response[1][0]['results'] = request.env[
                    'product.public.category'].browse(category)
                response[1][-1]['results'] = request.env[
                    'product.template'].browse(products)
        return tuple(response)

    def available_products(self):
        """Returns the available product (product.template) ids"""
        user = request.env['res.users'].sudo().search(
            [('id', '=', request.env.user.id)])
        partner = request.env['res.partner'].sudo().search(
            [('id', '=', user.partner_id.id)])
        return partner.website_available_product_ids
