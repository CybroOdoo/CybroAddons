from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Boolean(string="Sale Order Approval")
