from odoo import models,fields,api


class ProductBrand(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand',string='Brand')

class BrandProduct(models.Model):
    _name = 'product.brand'


    name= fields.Char(String="Name")
    brand_image = fields.Binary()
    member_ids = fields.One2many('product.template','brand_id')
    product_count = fields.Char(String='Product Count',compute='get_count_products',store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)

class BrandPivot(models.Model):
    _inherit = 'sale.report'

    brand_id=fields.Many2one ('product.brand' ,string='Brand')

    def _query(self):
        res= super(BrandPivot, self)._query()
        query = res.split('t.categ_id as categ_id,',1)
        query= query[0]+'t.categ_id as categ_id,t.brand_id as brand_id,' +query[1]
        split= query.split('t.categ_id,',1)
        res = split[0] + 't.categ_id,t.brand_id,' + split[1]
        return res

