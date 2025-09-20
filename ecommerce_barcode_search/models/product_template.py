# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1.0,
            parent_combination=False, only_template=False, is_barcode=False
    ):

        res = super()._get_combination_info(combination=combination, product_id=product_id, add_qty=add_qty,
            parent_combination=parent_combination, only_template=only_template)
        if is_barcode:
            if request.session.get('barcode'):
                product = self.env['product.product'].search([('barcode', '=', request.session.get('barcode'))])
                if product:
                    res.update({
                        'combination': [each for each in product.product_template_attribute_value_ids],
                    })
        return res
