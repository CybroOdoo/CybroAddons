# -*- coding: utf-8 -*-

from openerp import fields, models

class MultiProductImagesRel(models.Model):
    _name = 'product.images'
    _description = "Add Multiple Images in Product"

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name')
    image = fields.Binary(
        'Image',
        attachment=True,
    )
    product_id_rel = fields.Many2one(
        'product.template',
        'Product',
    )

class Product(models.Model):
    _inherit = 'product.template'
    _description = "Images Gallery For Products"

    product_multi_images = fields.One2many(
        'product.images',
        'product_id_rel',
        string='Gallery',
    )