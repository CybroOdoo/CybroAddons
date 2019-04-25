from odoo import models, api, fields


class GatePass(models.Model):
    _inherit = 'stock.picking'

    enable_order_line = fields.Boolean(string='Include Product Details', default=True)
    vehicle_no = fields.Char(string='Vehicle Number')
    vehicle_driver_name = fields.Char(string='Driver Name')
    driver_contact_number = fields.Char(string='Contact No')
    corresponding_company = fields.Char(string='Company')

