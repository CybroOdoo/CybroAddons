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
from odoo import fields, models


class ProductPublish(models.TransientModel):
    """ Wizard for multiple product publish in product template """
    _name = 'product.publish'
    _description = "Product Publish/Unpublish"

    product_ids = fields.Many2many(
        'product.template',
        string='Products'
    )

    def action_product_multi_publish(self):
        """Function for publishing selected products on the website."""
        products = self.product_ids.filtered(
            lambda product: product.sale_ok
        )
        products.write({'is_published': True})

    def action_product_multi_unpublish(self):
        """Function for unpublishing selected products from the website."""
        self.product_ids.filtered('sale_ok').write({
            'is_published': False
        })
