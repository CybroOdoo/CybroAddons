from odoo import fields, models


class MailerCloudList(models.Model):
    _name = 'mailer.cloud.list'

    mailer_cloud_id = fields.Char()
    name = fields.Char(string='Name')
    authorization_id = fields.Many2one('mailer.cloud.api.sync')
