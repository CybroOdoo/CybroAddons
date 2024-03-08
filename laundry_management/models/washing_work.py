from odoo import models, fields


class ExtraWork(models.Model):
    """
        model for creating extra work for washing.
    """
    _name = 'washing.work'
    _description = 'Washing Work'

    name = fields.Char(string='Name', required=1)
    assigned_person = fields.Many2one('res.users',
                                      string='Assigned Person', required=1,
                                      help="name of assigned person")
    amount = fields.Float(string='Service Charge', required=1)
