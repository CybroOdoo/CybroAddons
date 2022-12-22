from odoo import fields, models, api
from odoo.exceptions import ValidationError
import requests
import json


class InheritContacts(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Char(string='partner_type',
                               compute='_compute_partner_type')
    mailer_cloud_id = fields.Char()

    def _compute_partner_type(self):
        # computing partner type based on sale_order_count and purchase_order_count
        for rec in self:
            if rec.sale_order_count > 0 and rec.purchase_order_count > 0:
                rec.partner_type = "Vendor and Customer"
            elif rec.sale_order_count > 0:
                rec.partner_type = "Customer"
            elif rec.purchase_order_count > 0:
                rec.partner_type = "Vendor"
            else:
                rec.partner_type = None

    @api.model
    def create(self, vals_list):
        res = super(InheritContacts, self).create(vals_list)
        contact_sync = self.env['mailer.cloud.api.sync'].search(
            [('contact_sync_active', '=', True)],
            order='contact_sync_time desc', limit=1)
        if contact_sync:
            try:
                for rec in contact_sync:
                    contact_details_dict = {}
                    contact_details_dict.clear()
                    for i in range(
                            len(rec.contact_mapping_ids.mapped(
                                'property_id.name'))):
                        if self.env['mailer.cloud.properties'].search(
                                [('id', '=',
                                  rec.contact_mapping_ids.mapped(
                                      'property_id')[
                                      i].id)]).mailer_cloud_id != False:
                            contact_details_dict['custom_fields'] = {
                                rec.contact_mapping_ids.mapped(
                                    'property_id.mailer_cloud_id')[i]:
                                    res.read([
                                        rec.contact_mapping_ids.mapped(
                                            'contact_fields')[i]])[0][
                                        rec.contact_mapping_ids.mapped(
                                            'contact_fields')[i]] or ' '}
                            for key, value in contact_details_dict[
                                'custom_fields'].items():
                                if isinstance(value, float):
                                    contact_details_dict[
                                        'custom_fields'].update(
                                        {key: round(value)})

                        else:
                            contact_details_dict[
                                rec.contact_mapping_ids.mapped(
                                    'property_id.name')[
                                    i]] = res.read([
                                rec.contact_mapping_ids.mapped(
                                    'contact_fields')[i]])[0][
                                              rec.contact_mapping_ids.mapped(
                                                  'contact_fields')[i]] or ' '
                            for key, value in contact_details_dict.items():
                                if isinstance(value, float):
                                    contact_details_dict.update(
                                        {key: round(value)})
                    contact_details_dict[
                        'list_id'] = rec.list_id.mailer_cloud_id
                    url = "https://cloudapi.mailercloud.com/v1/contacts"
                    payload = json.dumps(contact_details_dict)
                    headers = {
                        'Authorization': rec.api_key,
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("POST", url, headers=headers,
                                                data=payload)
                    if response.status_code in (400, 401):
                        raise ValidationError(
                            response.json()['errors'][0]['message'])
            except Exception as e:
                raise ValidationError(e)
        return res

    def write(self, vals):
        res = super(InheritContacts, self).write(vals)
        contact_sync = self.env['mailer.cloud.api.sync'].search(
            [('contact_sync_active', '=', True)],
            order='contact_sync_time desc', limit=1)
        if contact_sync:
            update_dict = {}
            for key, vals in vals.items():
                for rec in contact_sync.contact_mapping_ids:
                    if key == rec.contact_fields and rec.property_id.mailer_cloud_id != False:
                        update_dict['custom_fields'] = {
                            rec.property_id.mailer_cloud_id: round(
                                vals) if type(vals) == float else vals}
                    elif key == rec.contact_fields:
                        update_dict[key] = round(vals) if type(
                            vals) == float else vals
                    else:
                        continue
            if len(update_dict) > 0:
                try:
                    url = "https://cloudapi.mailercloud.com/v1/contacts/" + self.email
                    payload = json.dumps(update_dict)
                    headers = {
                        'Authorization': contact_sync.api_key,
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("PUT", url, headers=headers,
                                                data=payload)

                except Exception as e:
                    raise ValidationError(e)
            else:
                pass
        return res
