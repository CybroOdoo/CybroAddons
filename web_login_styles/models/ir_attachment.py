from odoo import models, fields, api


class AttachmentFile(models.Model):
    _inherit = 'ir.attachment'

    is_background = fields.Boolean(string="Is Background", default=False)
