# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InheritContacts(models.Model):
    """
        Extends the base 'res.partner' model to include additional fields related to Mailercloud integration.

        This class inherits from the 'res.partner' model and adds custom fields for Mailercloud integration,
        including 'partner_type' and 'mailer_cloud'.
        """
    _inherit = 'res.partner'

    partner_type = fields.Char(
        string='Partner Type', compute='_compute_partner_type',
        help='Type of the partner, computed based on specific criteria.')
    mailer_cloud = fields.Char(string='Mailercloud',
                               help='Identifier for the partner in '
                                    'Mailercloud.')

    def _compute_partner_type(self):
        """
            Compute method to determine the 'partner_type' based on specific criteria.

            This method computes the 'partner_type' field based on certain conditions or criteria.
            """
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
        """
            Create method to extend the creation of 'res.partner' records and synchronize data with Mailercloud.

            This method is called when creating a new 'res.partner' record. It extends the base creation process
            to include synchronization with Mailercloud, if contact synchronization is active for any associated API.

            :param vals_list: List of dictionaries containing values for the new 'res.partner' record(s).
            :return: Created 'res.partner' record(s).
            :raises: ValidationError if there is an issue with the Mailercloud API synchronization.
            """
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
                        if self.env['mailer.cloud.properties'].search([('id', '=', rec.contact_mapping_ids.mapped(
                                'property_id')[i].id)]).mailer_cloud:
                            contact_details_dict['custom_fields'] = {
                                rec.contact_mapping_ids.mapped('property_id.mailer_cloud')[i]:
                                    res.read([rec.contact_mapping_ids.mapped('contact_fields')[i]])[0][
                                        rec.contact_mapping_ids.mapped('contact_fields')[i]] or ' '}
                            for key, value in contact_details_dict['custom_fields'].items():
                                if isinstance(value, float):
                                    contact_details_dict[
                                        'custom_fields'].update(
                                        {key: round(value)})
                        else:
                            contact_details_dict[
                                rec.contact_mapping_ids.mapped(
                                    'property_id.name')[
                                    i]] = res.read([rec.contact_mapping_ids.mapped('contact_fields')[i]])[0][
                                              rec.contact_mapping_ids.mapped('contact_fields')[i]] or ' '
                            for key, value in contact_details_dict.items():
                                if isinstance(value, float):
                                    contact_details_dict.update(
                                        {key: round(value)})
                    contact_details_dict[
                        'list_id'] = rec.list_id.mailer_cloud
                    url = "https://cloudapi.mailercloud.com/v1/contacts"
                    payload = json.dumps(contact_details_dict)
                    headers = {
                        'Authorization': rec.api_key,
                        'Content-Type': 'application/json'
                    }
                    response = requests.request("POST", url, headers=headers, data=payload)
                    if response.status_code in (400, 401):
                        raise ValidationError(
                            response.json()['errors'][0]['message'])
            except Exception as e:
                raise ValidationError(e)
        return res

    def write(self, vals):
        """
            Extend the standard write method for 'res.partner' records and synchronize updates with Mailercloud.

            This method is called when updating an existing 'res.partner' record. It extends the base write process
            to include synchronization with Mailercloud if contact synchronization is active for any associated API.

            :param vals: Dictionary of field-value pairs to update for the 'res.partner' record.
            :return: Result of the standard write method.
            :raises: ValidationError if there is an issue with the Mailercloud API synchronization.
            """
        res = super(InheritContacts, self).write(vals)
        contact_sync = self.env['mailer.cloud.api.sync'].search(
            [('contact_sync_active', '=', True)], order='contact_sync_time desc', limit=1)
        if contact_sync:
            update_dict = {}
            for key, vals in vals.items():
                for rec in contact_sync.contact_mapping_ids:
                    if key == rec.contact_fields and rec.property_id.mailer_cloud:
                        update_dict['custom_fields'] = {
                            rec.property_id.mailer_cloud: round(vals) if type(vals) == float else vals}
                    elif key == rec.contact_fields:
                        update_dict[key] = round(vals) if type(vals) == float else vals
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
                    requests.request("PUT", url, headers=headers, data=payload)
                except Exception as e:
                    raise ValidationError(e)
            else:
                pass
        return res
