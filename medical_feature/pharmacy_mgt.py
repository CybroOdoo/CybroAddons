from openerp import models, fields,api


class Medicines(models.Model):
    _inherit = 'product.template'

    medicine_category = fields.Selection([('allopathy', 'Allopathy'),
                                            ('ayurvedic', 'Ayurvedic'),
                                            ('homeo', 'Homeo'),
                                            ('generic', 'Generic'),
                                            ('none', 'None Medicine'),
                                            ('veterinary', 'Veterinary'), ], 'Medicine Type', default='generic')
    medicine_type = fields.Many2one('product.medicine.types', 'Medicine Category')
    product_of = fields.Many2one('product.medicine.responsible', 'Product Of')


class MedicineTypes(models.Model):
    _name = 'product.medicine.types'
    _rec_name = 'medicine_type'

    medicine_type = fields.Char(string="Medicine Category")


class MedicineResponsible(models.Model):
    _name = 'product.medicine.responsible'
    _rec_name = 'name_responsible'

    name_responsible = fields.Char(string="Product Of ")
    related_vendor = fields.Many2one('res.partner', string='Related Vendor', domain="[('supplier', '=','1')]")
    place = fields.Char(string="Place")


