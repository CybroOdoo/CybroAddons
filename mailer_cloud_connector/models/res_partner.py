# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
import logging
import requests
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Extends the base 'res.partner' model to include additional fields related to Mailercloud integration.

    This class inherits from the 'res.partner' model and adds custom fields for Mailercloud integration,
    including 'partner_type' and 'mailer_cloud'.
    """
    _inherit = 'res.partner'

    partner_type = fields.Char(
        compute='_compute_partner_type',
        help='Type of the partner, computed based on specific criteria.')
    mailer_cloud = fields.Char(
        string='Mailercloud',
        help='Identifier for the partner in Mailercloud.')

    def _compute_partner_type(self):
        """
        Compute method to determine the 'partner_type' based on specific criteria.
        """
        for rec in self:
            sale_order_count = rec.sale_order_count if 'sale_order_count' in rec._fields else 0
            purchase_order_count = rec.purchase_order_count if 'purchase_order_count' in rec._fields else 0
            if sale_order_count > 0 and purchase_order_count > 0:
                rec.partner_type = "Vendor and Customer"
            elif sale_order_count > 0:
                rec.partner_type = "Customer"
            elif purchase_order_count > 0:
                rec.partner_type = "Vendor"
            else:
                rec.partner_type = False

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create method to extend the creation of 'res.partner' records and synchronize data with Mailercloud.

        :param vals_list: List of dictionaries containing values for the new 'res.partner' record(s).
        :return: Created 'res.partner' record(s).
        """
        res = super().create(vals_list)
        contact_sync = self.env['mailer.cloud.api.sync'].sudo().search(
            [('contact_sync_active', '=', True)],
            order='contact_sync_time desc', limit=1)
        if contact_sync:
            for partner in res:
                if not partner.email:
                    continue
                try:
                    for rec in contact_sync:
                        contact_details_dict = {}
                        for mapping in rec.contact_mapping_ids:
                            field_name = mapping.contact_fields
                            field_val = partner[field_name] if field_name in partner._fields else False
                            if isinstance(field_val, float):
                                field_val = round(field_val)
                            elif not field_val:
                                field_val = ''
                            else:
                                field_val = str(field_val) if not isinstance(field_val, (int, str, bool)) else field_val

                            if mapping.property_id.mailer_cloud:
                                if 'custom_fields' not in contact_details_dict:
                                    contact_details_dict['custom_fields'] = {}
                                contact_details_dict['custom_fields'][mapping.property_id.mailer_cloud] = field_val
                            else:
                                contact_details_dict[mapping.property_id.name] = field_val

                        if 'email' not in contact_details_dict:
                            contact_details_dict['email'] = partner.email

                        if rec.list_id and rec.list_id.mailer_cloud:
                            contact_details_dict['list_id'] = rec.list_id.mailer_cloud

                        url = "https://cloudapi.mailercloud.com/v1/contacts"
                        payload = json.dumps(contact_details_dict)
                        headers = {
                            'Authorization': rec.api_key,
                            'Content-Type': 'application/json'
                        }
                        response = requests.request(
                            "POST", url, headers=headers, data=payload, timeout=30)
                        if response.status_code >= 400:
                            _logger.warning(
                                "Failed to create contact %s on Mailercloud (status %s): %s",
                                partner.email, response.status_code, response.text)
                except Exception as e:
                    _logger.exception("Error syncing contact %s to Mailercloud: %s", partner.email, e)
        return res

    def write(self, vals):
        """
        Extend the standard write method for 'res.partner' records and synchronize updates with Mailercloud.

        :param vals: Dictionary of field-value pairs to update for the 'res.partner' record.
        :return: Result of the standard write method.
        """
        old_emails = {partner.id: partner.email for partner in self}
        res = super().write(vals)
        contact_sync = self.env['mailer.cloud.api.sync'].sudo().search(
            [('contact_sync_active', '=', True)], order='contact_sync_time desc', limit=1)
        if contact_sync:
            for partner in self:
                if not partner.email:
                    continue
                old_email = old_emails.get(partner.id)
                update_dict = {}
                for key, val in vals.items():
                    for rec in contact_sync.contact_mapping_ids:
                        if key == rec.contact_fields:
                            val_to_send = round(val) if isinstance(val, float) else val
                            if rec.property_id.mailer_cloud:
                                if 'custom_fields' not in update_dict:
                                    update_dict['custom_fields'] = {}
                                update_dict['custom_fields'][rec.property_id.mailer_cloud] = val_to_send
                            else:
                                update_dict[key] = val_to_send
                if 'email' in vals and 'email' not in update_dict:
                    update_dict['email'] = partner.email

                if update_dict:
                    try:
                        if not old_email:
                            contact_details_dict = {}
                            for mapping in contact_sync.contact_mapping_ids:
                                field_name = mapping.contact_fields
                                field_val = partner[field_name] if field_name in partner._fields else False
                                if isinstance(field_val, float):
                                    field_val = round(field_val)
                                elif not field_val:
                                    field_val = ''
                                else:
                                    field_val = str(field_val) if not isinstance(field_val, (int, str, bool)) else field_val

                                if mapping.property_id.mailer_cloud:
                                    if 'custom_fields' not in contact_details_dict:
                                        contact_details_dict['custom_fields'] = {}
                                    contact_details_dict['custom_fields'][mapping.property_id.mailer_cloud] = field_val
                                else:
                                    contact_details_dict[mapping.property_id.name] = field_val
                            if 'email' not in contact_details_dict:
                                contact_details_dict['email'] = partner.email
                            if contact_sync.list_id and contact_sync.list_id.mailer_cloud:
                                contact_details_dict['list_id'] = contact_sync.list_id.mailer_cloud

                            url = "https://cloudapi.mailercloud.com/v1/contacts"
                            payload = json.dumps(contact_details_dict)
                            headers = {
                                'Authorization': contact_sync.api_key,
                                'Content-Type': 'application/json'
                            }
                            response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
                            if response.status_code >= 400:
                                _logger.warning(
                                    "Failed to create contact %s on Mailercloud (status %s): %s",
                                    partner.email, response.status_code, response.text)
                        else:
                            url = "https://cloudapi.mailercloud.com/v1/contacts/" + old_email
                            payload = json.dumps(update_dict)
                            headers = {
                                'Authorization': contact_sync.api_key,
                                'Content-Type': 'application/json'
                            }
                            response = requests.request(
                                "PUT", url, headers=headers, data=payload, timeout=30)
                            if response.status_code >= 400:
                                _logger.warning(
                                    "Failed to update contact %s on Mailercloud (status %s): %s",
                                    old_email, response.status_code, response.text)
                    except Exception as e:
                        _logger.exception("Error updating contact %s on Mailercloud: %s", partner.email, e)
        return res
