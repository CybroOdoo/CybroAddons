from odoo import models,fields,api,tools


class ProductBrand(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand',string='Brand')

class BrandProduct(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'

    name= fields.Char(String="Name")
    brand_image = fields.Binary()
    member_ids = fields.One2many('product.template','brand_id')
    product_count = fields.Char(String='Product Count',compute='get_count_products',store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)

class PurchaseBrandPivot(models.Model):
    _inherit = 'purchase.report'

    brand_id = fields.Many2one('product.brand',string='Brand')


    def _select(self):
        res = super(PurchaseBrandPivot,self)._select()
        query = res.split('t.categ_id as category_id,',1)
        rese = query[0] + 't.categ_id as category_id,t.brand_id as brand_id,' + query[1]
        return rese



    def _group_by(self):
        res=super (PurchaseBrandPivot ,self)._group_by ()
        query = res.split('t.categ_id,',1)
        res = query[0] + 't.categ_id,t.brand_id,' + query[1]
        print(res)
        return res
