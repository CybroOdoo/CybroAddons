from odoo import fields, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    status = fields.Char("Status of the mail")
    to = fields.Char("To")
