from odoo import models, fields


class WashingType(models.Model):
    """washing types generating model"""
    _name = 'washing.type'
    _description = "Washing TYpe"

    name = fields.Char(string='Name', required=1)
    assigned_person = fields.Many2one('res.users',
                                      string='Assigned Person', required=1,
                                      help="name of assigned person")
    amount = fields.Float(string='Service Charge', required=1)
