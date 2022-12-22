from odoo import fields, models, api
import json
import requests


class MailerCloudList(models.Model):
    _name = 'mailer.cloud.properties'

    mailer_cloud_id = fields.Char()
    name = fields.Char(string='Property Name', required=True)
    type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('textarea', 'Textarea')], string='Type', required=True)
    authorization_id = fields.Many2one('mailer.cloud.api.sync',
                                       ondelete='cascade')

    @api.model
    def create(self, vals_list):
        res = super(MailerCloudList, self).create(vals_list)
        try:
            url = "https://cloudapi.mailercloud.com/v1/contact/property"

            payload = json.dumps({
                "name": res.name,
                "type": res.type
            })
            headers = {
                'Authorization': res.authorization_id.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            res.write({
                'mailer_cloud_id': response.json()['id']
            })
        except Exception as e:
            pass
        return res
