from odoo import fields, models


class SelectionMessages(models.Model):
    _name = 'selection.messages'

    name = fields.Char(string='Name of the Message Template')
    message = fields.Text(string="Message", required=True)

