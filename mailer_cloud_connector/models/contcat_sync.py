from odoo import fields, models


class ContactContactSync(models.Model):
    _name = 'contact.sync'

    property_id = fields.Many2one('mailer.cloud.properties', required=True,
                                  string='Mailer Cloud Properties')
    contact_fields = fields.Selection(
        selection=lambda self: self.dynamic_selection(), required=True,
        string='Odoo fields')
    sync_id = fields.Many2one('mailer.cloud.api.sync')

    def dynamic_selection(self):
        select = []
        for key in self.env['res.partner'].fields_get().keys():
            select.append((key, key.capitalize()))
        return select
