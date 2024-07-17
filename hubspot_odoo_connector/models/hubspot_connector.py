# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from datetime import datetime, timezone
from hubspot import HubSpot
from hubspot.crm.deals import BatchInputSimplePublicObjectBatchInput
from hubspot.crm.deals import SimplePublicObjectInput
import requests
from odoo import fields, models, _
from odoo.exceptions import AccessError
import pytz



class HubspotConnector(models.Model):
    """
    Model for hubspot connector to set up the credentials and contains
    methods for various sync operations.
    Methods:
        action_connect(self):
            CONNECT smart button action to check the hubspot account with
            provided credentials, if account exist it connects, and shows the
            sync options.
        action_contact_sync(self):
            Button action for sync contacts based on user preference.
        action_company_sync(self):
            Button action for sync company based on user preference.
        action_deal_sync(self):
            Button action for sync deals based on user preference.
        #--- Contacts Various Sync Methods ---#
        action_export_partner(self):
            Method for exporting contacts when the contact is not available in
            hubspot.
        action_import_partner(self):
            Method for importing contacts when the contact is not available in
            odoo.
        action_update_hub_partner(self):
            Method for update contacts in hubspot, based on odoo contacts,
        action_update_odoo_partner(self):
            Method for update contacts in odoo, based on hubspot contacts,
        #--- Various Sync Methods for Company ---#
        action_export_company(self):
            Method for exporting company when the company is not available in
            hubspot.
        action_import_company(self):
            Method for importing company when the company is not available in
            odoo.
        action_update_hub_company(self):
            Method for update company in hubspot, based on odoo company.
        action_update_odoo_company(self):
            Method for update company in odoo, based on hubspot company.
        #--- Various Sync Methods for Deals ---#
        action_export_deals(self):
            Method for exporting deals when the deals are not available in
            hubspot.
        action_import_deals(self):
            Method for importing deals when the deals are not available in
            odoo.
        action_update_hub_deals(self):
            Method for update deals in hubspot, based on odoo deals.
        action_update_odoo_deals(self):
            Method for update deals in odoo, based on hubspot deals.
    """
    _name = 'hubspot.connector'
    _description = 'HubSpot Connector'

    state = fields.Selection(string="State",
                             selection=[("disconnected", "Disconnected"),
                                        ("connected", "Connected")],
                             default="disconnected",
                             help="Shows the connection is true or false")
    name = fields.Char(string="Connector Name", help="name of the instance")
    access_key = fields.Char(string="Access Token",
                             help="Private app key of hubspot account")
    owner_id = fields.Char(string="Owner ID", required=True,
                           help="Owner ID of Hubspot account")
    connection = fields.Boolean(string="Connection",
                                help="Shows connected to hubspot or nor")
    # Toggles for Contacts sync
    import_contacts = fields.Boolean(string="Import Contacts",
                                     help="This will enable import of contact "
                                          "from hubspot to odoo")
    export_contacts = fields.Boolean(string="Export Contacts",
                                     help="This will enable export of contact "
                                          "from odoo to hubspot")
    update_odoo_contacts = fields.Boolean(string="Update Odoo Contacts",
                                          help="This will update contact in "
                                               "odoo from hubspot data")
    update_hub_contacts = fields.Boolean(string="Update Hubspot Contacts",
                                         help="This will update contact in "
                                              "hubspot from odoo data")
    # Toggles for Company sync
    import_company = fields.Boolean(string="Import Company",
                                    help="This will enable import of companies"
                                         "from hubspot to odoo")
    export_company = fields.Boolean(string="Export Company",
                                    help="This will enable export of companies "
                                         "from Odoo to HubSpot")
    update_odoo_company = fields.Boolean(string="Update Odoo Company",
                                         help="This will update company in odoo"
                                              "from hubspot data")
    update_hub_company = fields.Boolean(string="Update Hubspot Company",
                                        help="This will update company in "
                                             "hubspot from odoo data")
    # Toggles for Deals sync
    export_deals = fields.Boolean(
        string="Export Deals",
        help="This will enable export of deals from odoo to hubspot")
    import_deals = fields.Boolean(
        string="Import Deals",
        help="This will enable import of deals from hubspot to odoo")
    update_odoo_deals = fields.Boolean(
        string="Update Odoo Deals",
        help="This will update deals in odoo from hubspot data")
    update_hub_deals = fields.Boolean(
        string="Update Hubspot Deals",
        help="This will update deals in hubspot from odoo data")
    # Contacts last sync Times
    contacts_last_imported = fields.Datetime(
        string="Contact Last Imported", readonly=True,
        help="This is the last imported time")
    contacts_last_exported = fields.Datetime(
        string="Contact Last Exported", readonly=True,
        help="This is the last exported time")
    hub_contact_last_updated = fields.Datetime(
        string="Hubspot Contacts Updated", readonly=True,
        help="Last Hubspot Contacts Updated Time")
    odoo_contact_last_updated = fields.Datetime(
        string="Odoo Contacts Updated", readonly=True,
        help="Last Odoo Contacts Updated Time")
    # Company last sync Times
    company_last_imported = fields.Datetime(
        string="Company Last Imported", readonly=True,
        help="This is the last imported time")
    company_last_exported = fields.Datetime(
        string="Company Last Exported", readonly=True,
        help="This is the last exported time")
    hub_company_last_updated = fields.Datetime(
        string="Hubspot Company Updated", readonly=True,
        help="Last Hubspot Company Updated Time")
    odoo_company_last_updated = fields.Datetime(
        string="Odoo Company Updated", readonly=True,
        help="Last Odoo Company Updated Time")
    # Deals last sync Times
    deals_last_imported = fields.Datetime(
        string="Deals Last Imported", readonly=True,
        help="This is the last imported time")
    deals_last_exported = fields.Datetime(
        string="Deals Last Exported", readonly=True,
        help="This is the last exported time")
    hub_deal_last_updated = fields.Datetime(
        string="Hubspot Deal Updated", readonly=True,
        help="Last Hubspot Deal Updated Time")
    odoo_deal_last_updated = fields.Datetime(
        string="Odoo Deal Updated", readonly=True,
        help="Last Odoo Deal Updated Time")

    def action_connect(self):
        """
        Method for testing connection; if credentials are correct connects
        and shows sync options, if connected disconnects.
        """
        if not self.connection:
            owners_endpoint = 'https://api.hubapi.com/owners/v2/owners'
            headers = {'Authorization': f'Bearer {self.access_key}'}
            try:
                response = requests.get(owners_endpoint, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if str(data[0]['ownerId']) == self.owner_id:
                        self.connection = True
                        self.state = "connected"
                else:
                    raise AccessError(_("Error when Fetching account info"))
            except requests.exceptions.RequestException:
                return None
        else:
            self.connection = False
            self.state = "disconnected"

    def action_contact_sync(self):
        """
        Method used to sync contacts it calls methods for import, export and
        update contacts methods when user need specific condition on sync
        """
        rainbow_msg = "Congrats, "
        if self.export_contacts:
            exported_count = self.action_export_partner()
            if exported_count > 0:
                rainbow_msg += f"# {exported_count} Contacts Exported"
        if self.import_contacts:
            imported_count = self.action_import_partner()
            if imported_count > 0:
                rainbow_msg += f", # {imported_count} Contacts Imported"
        if self.update_hub_contacts:
            hub_update_count = self.action_update_hub_partner()
            if hub_update_count > 0:
                rainbow_msg += f", #{hub_update_count} Hubspot Contacts Updated"
        if self.update_odoo_contacts:
            odoo_update_count = self.action_update_odoo_partner()
            if odoo_update_count > 0:
                rainbow_msg += f", # {odoo_update_count} Odoo Contacts Updated"
        # If there is no sync option modifies data
        if rainbow_msg == "Congrats, ":
            rainbow_msg += "Contacts are already synced"
        # Rainbow man displays status of sync
        return {
            'effect': {
                'fadeout': 'slow',
                'message': rainbow_msg,
                'type': 'rainbow_man'
            }
        }

    def action_company_sync(self):
        """
        Method used to sync company it calls methods for import, export and
        update company methods when user need specific condition on sync
        """
        rainbow_msg = "Congrats, "
        if self.export_company:
            exported_count = self.action_export_company()
            if exported_count > 0:
                rainbow_msg += f"# {exported_count} Companies Exported"
        if self.import_company:
            imported_count = self.action_import_company()
            if imported_count > 0:
                rainbow_msg += f", # {imported_count} Companies Imported"
        if self.update_hub_company:
            hub_update_count = self.action_update_hub_company()
            if hub_update_count > 0:
                rainbow_msg += (f", # {hub_update_count}"
                                f" Hubspot Companies Updated")
        if self.update_odoo_company:
            odoo_update_count = self.action_update_odoo_company()
            if odoo_update_count > 0:
                rainbow_msg += f", # {odoo_update_count} Odoo Companies Updated"
        if rainbow_msg == "Congrats, ":
            rainbow_msg += "Companies are already synced"
        return {
            'effect': {
                'fadeout': 'slow',
                'message': rainbow_msg,
                'type': 'rainbow_man'
            }
        }

    def action_deal_sync(self):
        """
        Method used to sync deals, it calls methods for import, export and
        update deals methods when user need specific condition on sync
        """
        rainbow_msg = "Congrats, "
        if self.export_deals:
            exported_count = self.action_export_deals()
            if exported_count > 0:
                rainbow_msg += f"# {exported_count} Deals Exported"
        if self.import_deals:
            imported_count = self.action_import_deals()
            if imported_count > 0:
                rainbow_msg += f", # {imported_count} Deals Imported"
        if self.update_hub_deals:
            hub_update_count = self.action_update_hub_deals()
            if hub_update_count > 0:
                rainbow_msg += f", # {hub_update_count} Hubspot Deals Updated"
        if self.update_odoo_deals:
            odoo_update_count = self.action_update_odoo_deals()
            if odoo_update_count > 0:
                rainbow_msg += f", # {odoo_update_count} Odoo Deals Updated"
        if rainbow_msg == "Congrats, ":
            rainbow_msg += "Deals are already synced"
        return {
            'effect': {
                'fadeout': 'slow',
                'message': rainbow_msg,
                'type': 'rainbow_man'
            }
        }

    def action_export_partner(self):
        """
        Method used to Export Contacts from Odoo to Hubspot, also creates
        non-existing odoo_mail and odoo_image_string fields which are not
        present in hubspot and export according data to it.
        """
        # Set up HubSpot API connection.
        api_key = self.access_key
        base_url = 'https://api.hubapi.com'
        # Lists fields and their properties need to create in hubspot.
        partner_fields = [
            {
                'name': 'odoo_mail',
                'label': 'Mail',
                'type': 'string'
            },
            {
                'name': 'odoo_image_string',
                'label': 'Image String',
                'type': 'string'
            },
        ]
        for field in partner_fields:
            # Check each field in partner_fields exists in HubSpot or not
            endpoint = f"/properties/v1/contacts/properties/named/" \
                       f"{field['name']}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            response = requests.get(base_url + endpoint, headers=headers)
            # Response returns a status code "200" when field exist in hubspot.
            if response.status_code != 200:
                # Create custom field in HubSpot
                endpoint = '/properties/v1/contacts/properties'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(api_key)
                }
                # Properties of Field ie, going to create
                payload = {
                    'name': field['name'],
                    'label': field['label'],
                    'description': 'Custom field created form odoo',
                    'groupName': 'contactinformation',
                    'type': field['type']
                }
                # API call for Field creation
                response = requests.post(base_url + endpoint, json=payload,
                                         headers=headers)
                # Returns status code "200" when successfully created the field
                if response.status_code == 200:
                    pass  # Notification : Successfully connected.
                else:
                    raise AccessError(f"Failed to create {field['name']} field,"
                                      f"Status code: {response.status_code}")
        # Setting api client connection via api
        api_client = HubSpot(access_token=self.access_key)
        odoo_partners = self.env['res.partner'].search([])
        success_count = 0
        # Fetch HubSpot contact's ID as list
        hubspot_partners = [rec.properties['hs_object_id']
                            for rec in api_client.crm.contacts.get_all()]
        for rec in odoo_partners:
            # If the Odoo contact not present in Hubspot ID list export it
            if rec.hs_object_id not in hubspot_partners:
                properties = {
                    "firstname": rec.name,
                    "lastname": "",
                    "odoo_mail": rec.email,
                    "phone": rec.phone if rec.phone else None,
                    "company": rec.commercial_company_name or rec.company_name
                    if rec.commercial_company_name or rec.company_name
                    else None,
                    "jobtitle": rec.function if rec.function else None,
                    "website": rec.website if rec.website else None,
                    "address": rec.street + "," + rec.street2 if (
                            rec.street and rec.street2) else (
                            rec.street or rec.street2 or ""),
                    "city": rec.city if rec.city else None,
                    "state": rec.state_id.name if rec.state_id else None,
                    "zip": rec.zip if rec.zip else None,
                    "country": rec.country_id.name if rec.country_id else None,
                    "odoo_image_string": base64.b64encode(rec.image_1920).
                    decode('utf-8') if (rec.image_1920 and len(base64.b64encode(
                        rec.image_1920).decode('utf-8')) < 65500) else None,
                }
                api_response = api_client.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=
                    SimplePublicObjectInput(properties))
                # If Exported then update Hubspot ID in Odoo
                if api_response:
                    rec.write({
                        'hs_object_id': api_response.properties['hs_object_id'],
                        'sync_mode': 'export'})
                else:
                    # change it to Failure msg.
                    pass
                success_count += 1
        # If Any record exported Create Sync History
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': datetime.now(),
                'res_model_id': self.env.ref('base.model_res_partner').id,
                'sync_mode': 'export',
                'state': 'success',
                'count': success_count,
            })
        self.contacts_last_exported = datetime.now()
        # Returns Exported Count
        return success_count

    def action_import_partner(self):
        """
        Method used fetch data from Hubspot and creates contacts based on it.
        """
        # Fields needs to fetch from hubspot.
        needed_fields = [
            "firstname", "lastname", "email", "phone", "company", "jobtitle",
            "website", "address", "city", "state", "zip", "country",
            "odoo_mail", "odoo_image_string", "hs_object_id"
        ]
        api_client = HubSpot(access_token=self.access_key)
        odoo_partners = self.env['res.partner'].search([]).mapped(
            'hs_object_id')
        # Getting needed fields from hubspot
        hubspot_partners = api_client.crm.contacts.get_all(
            properties=needed_fields)
        partners_to_create = []
        success_count = 0
        # Creates Dictionaries from country and state model to fetch
        # state_id and country_id
        state_dict = {state['name']: state['id'] for state in self.env[
            'res.country.state'].search_read([], ['name'])}
        country_dict = {country['name']: country['id'] for country in self.env[
            'res.country'].search_read([], ['name'])}
        for rec in hubspot_partners:
            # If hubspot record not present in odoo records creates it.
            if rec.properties['hs_object_id'] not in odoo_partners:
                partners_to_create.append({
                    'name': rec.properties['firstname'] + '' + rec.properties[
                        'lastname'] if rec.properties[
                        'lastname'] else rec.properties['firstname'],
                    'email': rec.properties['email'] if rec.properties[
                        'email'] else rec.properties[
                        'odoo_mail'] if rec.properties['odoo_mail'] else None,
                    'phone': rec.properties['phone'],
                    'function': rec.properties['jobtitle'],
                    'website': rec.properties['website'],
                    'street': rec.properties['address'],
                    'city': rec.properties['city'],
                    'zip': rec.properties['zip'],
                    'state_id': state_dict.get(str(rec.properties['state']),
                                               None),
                    'country_id': country_dict.get(
                        str(rec.properties['country']), None),
                    'image_1920': base64.b64decode(
                        rec.properties['odoo_image_string']) if rec.properties[
                        'odoo_image_string'] else None,
                    'hs_object_id': rec.properties['hs_object_id'],
                    'sync_mode': 'import'
                })
                # counting total records created
                success_count += 1
        if partners_to_create:
            self.env['res.partner'].sudo().create(partners_to_create)
        # If new record created, then creates sync history.
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': datetime.now(),
                'res_model_id': self.env.ref('base.model_res_partner').id,
                'sync_mode': 'import',
                'state': 'success',
                'count': success_count,
            })
        self.contacts_last_imported = datetime.now()
        return success_count

    def action_update_hub_partner(self):
        """ Method used to update hubspot contacts based on odoo contacts. """
        api_client = HubSpot(access_token=self.access_key)
        odoo_partners = self.env['res.partner'].search([])
        odoo_partners_list = odoo_partners.mapped('hs_object_id')
        hubspot_partners = api_client.crm.contacts.get_all()
        update_success = 0
        data_to_update = []
        for rec in hubspot_partners:
            # Checking the hubspot contact present in odoo
            # then take the corresponding odoo record
            if rec.properties['hs_object_id'] in odoo_partners_list:
                odoo_record = self.env['res.partner'].search(
                    [('hs_object_id', '=', rec.properties['hs_object_id'])])
                # If the corresponding odoo record is last updated then
                # update hubspot record based on that
                if odoo_record.write_date > (
                        self.hub_contact_last_updated or rec.updated_at.
                        astimezone(timezone.utc).replace(tzinfo=None)):
                    data_to_update.append({
                        'id': rec.properties['hs_object_id'],
                        'properties': {
                            "firstname": odoo_record.name,
                            "lastname": "",
                            "odoo_mail": odoo_record.email,
                            "phone": odoo_record.phone,
                            "company": odoo_record.commercial_company_name
                                       or odoo_record.company_name,
                            "jobtitle": odoo_record.function,
                            "website": odoo_record.website,
                            "address": odoo_record.street + "," +
                                       odoo_record.street2 if (
                                    odoo_record.street and odoo_record.street2)
                            else (odoo_record.street
                                  or odoo_record.street2 or ""),
                            "city": odoo_record.city if odoo_record.city
                            else None,
                            "state": odoo_record.state_id.name
                            if odoo_record.state_id else None,
                            "zip": odoo_record.zip if odoo_record.zip else None,
                            "country": odoo_record.country_id.name
                            if odoo_record.country_id else None,
                            "odoo_image_string": base64.b64encode(
                                odoo_record.image_1920).decode('utf-8') if (
                                    odoo_record.image_1920 and len(
                                base64.b64encode(
                                    odoo_record.image_1920).decode(
                                    'utf-8')) < 65500) else "",
                        }
                    })
                    update_success += 1
        # Batch Update of record to hubspot.
        api_client.crm.contacts.batch_api.update(
            batch_input_simple_public_object_batch_input=
            BatchInputSimplePublicObjectBatchInput(data_to_update))
        self.hub_contact_last_updated = datetime.now()
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.hub_contact_last_updated,
                'res_model_id': self.env.ref('base.model_res_partner').id,
                'sync_mode': 'hub_updated',
                'state': 'success',
                'count': update_success,
            })
        # Returns successfully updated count.
        return update_success

    def action_update_odoo_partner(self):
        """Method used to update odoo partner based on the hubspot contacts."""
        api_client = HubSpot(access_token=self.access_key)
        odoo_partners = self.env['res.partner'].search([])
        # Fields need to fetch from hubspot.
        needed_fields = [
            "firstname", "lastname", "email", "phone", "company", "jobtitle",
            "website", "address", "city", "state", "zip", "country",
            "odoo_mail", "odoo_image_string", "hs_object_id"
        ]
        hubspot_partners = api_client.crm.contacts.get_all(
            properties=needed_fields)
        hubspot_partners_list = [rec.properties['hs_object_id']
                                 for rec in hubspot_partners]
        update_success = 0
        # Creates Dictionaries from country and state model to fetch
        # state_id and country_id
        state_dict = {state['name']: state['id'] for state in self.env[
            'res.country.state'].search_read([], ['name'])}
        country_dict = {country['name']: country['id'] for country in self.env[
            'res.country'].search_read([], ['name'])}
        for rec in odoo_partners:
            # If odoo record present in hubspot record then teke
            # corresponding hubspot record
            if rec.hs_object_id in hubspot_partners_list:
                hubspot_partner = {h.id: h for h in hubspot_partners}
                hub_record = hubspot_partner.get(rec.hs_object_id, None)
                # If hubspot record is recently updated, then update
                # odoo record based on that
                if hub_record.updated_at.astimezone(timezone.utc).replace(
                        tzinfo=None) > (
                        self.odoo_contact_last_updated or rec.write_date):
                    data_to_update = {
                        'name': hub_record.properties[
                                    'firstname'] + '' + hub_record.properties[
                                    'lastname'] if hub_record.properties[
                            'lastname'] else hub_record.properties['firstname'],
                        'email': hub_record.properties[
                            'email'] if hub_record.properties[
                            'email'] else hub_record.properties[
                            'odoo_mail'] if hub_record.properties[
                            'odoo_mail'] else None,

                        'phone': hub_record.properties['phone'],
                        'function': hub_record.properties['jobtitle'],
                        'website': hub_record.properties['website'],
                        'street': hub_record.properties['address'],
                        'city': hub_record.properties['city'],
                        'zip': hub_record.properties['zip'],
                        'state_id': state_dict.get(str(hub_record.properties[
                                                           'state']), None),
                        'country_id': country_dict.get(
                            str(hub_record.properties['country']), None),

                        'image_1920': base64.b64decode(
                            hub_record.properties[
                                'odoo_image_string']) if hub_record.properties[
                            'odoo_image_string'] else None,
                    }
                    update_success += 1
                    rec.write(data_to_update)
        self.odoo_contact_last_updated = datetime.now()
        # If there is any contact updated then creates sync history.
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.odoo_contact_last_updated,
                'res_model_id': self.env.ref('base.model_res_partner').id,
                'sync_mode': 'odoo_updated',
                'state': 'success',
                'count': update_success,
            })
        # Returns updated record's count.
        return update_success

    def action_export_company(self):
        """ Method to export companies to hubspot. """
        api_client = HubSpot(access_token=self.access_key)
        odoo_companies = self.env['res.company'].search([])
        hubspot_companies = []
        success_count = 0
        for rec in api_client.crm.companies.get_all():
            hubspot_companies.append(rec.properties['hs_object_id'])
        for rec in odoo_companies:
            # If odoo record not present in hubspot record create it
            # via api call
            if rec.hs_object_id not in hubspot_companies:
                properties = {
                    "name": rec.name,
                    "domain": rec.website,
                    "description": rec.company_details if rec.company_details
                    else None,
                    "phone": rec.phone,
                    "address": rec.street + "," + rec.street2 if (
                            rec.street and rec.street2) else (
                            rec.street or rec.street2 or ""),
                    "city": rec.city,
                    "state": rec.state_id.name if rec.state_id else None,
                    "zip": rec.zip if rec.zip else None,
                    "country": rec.country_id.name if rec.country_id else None,
                    "industry": "",
                }
                # API call for create company record on hubspot.
                api_response = api_client.crm.companies.basic_api.create(
                    simple_public_object_input_for_create=
                    SimplePublicObjectInput(properties))
                # After exporting save the unique hubspot id on that record
                if api_response:
                    rec.write({
                        'hs_object_id': api_response.properties['hs_object_id'],
                        'sync_mode': 'export'
                    })
                success_count += 1
        self.company_last_exported = datetime.now()
        # If there is any record exported then creates history record.
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.company_last_exported,
                'res_model_id': self.env.ref('base.model_res_company').id,
                'sync_mode': 'export',
                'state': 'success',
                'count': success_count,
            })
        # Returns the exported count.
        return success_count

    def action_import_company(self):
        """ Method to Import record from hubspot """
        api_client = HubSpot(access_token=self.access_key)
        odoo_companies = self.env['res.company'].search([]).mapped(
            'hs_object_id')
        # The fields need to fetch from hubspot.
        needed_fields = [
            "hs_object_id", "name", "domain", "website", "description", "phone",
            "city", "state", "country", "zip"
        ]
        hubspot_companies = api_client.crm.companies.get_all(
            properties=needed_fields)
        companies_to_create = []
        success_count = 0
        # Creates Dictionaries from country and state model to fetch
        # state_id and country_id
        state_dict = {state['name']: state['id'] for state in self.env[
            'res.country.state'].search_read([], ['name'])}
        country_dict = {country['name']: country['id'] for country in self.env[
            'res.country'].search_read([], ['name'])}
        for rec in hubspot_companies:
            # If hubspot record not present in odoo record, create new record.
            if rec.properties['hs_object_id'] not in odoo_companies:
                companies_to_create.append({
                    'name': rec.properties['name'],
                    'website': rec.properties['domain'],
                    'company_details': rec.properties['description'],
                    'phone': rec.properties['phone'],
                    'city': rec.properties['city'],
                    'state_id': state_dict.get(str(rec.properties['state']),
                                               None),
                    'country_id': country_dict.get(
                        str(rec.properties['country']), None),
                    'zip': rec.properties['zip'],
                    'hs_object_id': rec.properties['hs_object_id'],
                    'sync_mode': 'import',
                })
                success_count += 1
        if companies_to_create:
            self.env['res.company'].sudo().create(companies_to_create)
        self.deals_last_imported = datetime.now()
        # If any new record created then create history record.
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.deals_last_imported,
                'res_model_id': self.env.ref('base.model_res_company').id,
                'sync_mode': 'import',
                'state': 'success',
                'count': success_count,
            })
        # Returns the created record count.
        return success_count

    def action_update_hub_company(self):
        """ Method to update hubspot record based on odoo records """
        api_client = HubSpot(access_token=self.access_key)
        odoo_company = self.env['res.company'].search([])
        odoo_company_list = odoo_company.mapped('hs_object_id')
        hubspot_company = api_client.crm.companies.get_all()
        update_success = 0
        data_to_update = []
        for rec in hubspot_company:
            # If hubspot record present in odoo record then take
            # corresponding odoo record
            if rec.properties['hs_object_id'] in odoo_company_list:
                odoo_record = self.env['res.company'].search(
                    [('hs_object_id', '=', rec.properties['hs_object_id'])])
                # If odoo record is recently updated then update hubspot record.
                if odoo_record.write_date > (
                        self.hub_company_last_updated or rec.updated_at.
                        astimezone(timezone.utc).replace(tzinfo=None)):
                    data_to_update.append({
                        'id': rec.properties['hs_object_id'],
                        'properties': {
                            "name": odoo_record.name,
                            "domain": odoo_record.website,
                            "description": odoo_record.company_details
                            if odoo_record.company_details else None,
                            "phone": odoo_record.phone,
                            "address": odoo_record.street + "," +
                                       odoo_record.street2
                            if (odoo_record.street and odoo_record.street2)
                            else (odoo_record.street
                                  or odoo_record.street2 or ""),
                            "city": odoo_record.city,
                            "state": odoo_record.state_id.name
                            if odoo_record.state_id else None,
                            "zip": odoo_record.zip if odoo_record.zip else None,
                            "country": odoo_record.country_id.name
                            if odoo_record.country_id else None,
                            "industry": "",
                        }
                    })
                    update_success += 1
        api_client.crm.companies.batch_api.update(
            batch_input_simple_public_object_batch_input=
            BatchInputSimplePublicObjectBatchInput(data_to_update))
        self.hub_company_last_updated = datetime.now()
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.hub_company_last_updated,
                'res_model_id': self.env.ref('base.model_res_company').id,
                'sync_mode': 'hub_updated',
                'state': 'success',
                'count': update_success,
            })
        # Returns the updated count.
        return update_success

    def action_update_odoo_company(self):
        """ Method to update odoo company records based on hubspot record. """
        api_client = HubSpot(access_token=self.access_key)
        odoo_company = self.env['res.company'].search([])
        # Needed fields to fetch from hubspot.
        needed_fields = [
            "hs_object_id", "name", "domain", "website", "description", "phone",
            "city", "state", "country", "zip"
        ]
        hubspot_company = api_client.crm.companies.get_all(
            properties=needed_fields)
        hubspot_company_list = [rec.properties['hs_object_id']
                                for rec in hubspot_company]
        update_success = 0
        # Creates Dictionaries from country and state model to fetch
        # state_id and country_id.
        state_dict = {state['name']: state['id'] for state in self.env[
            'res.country.state'].search_read([], ['name'])}
        country_dict = {country['name']: country['id'] for country in self.env[
            'res.country'].search_read([], ['name'])}
        for rec in odoo_company:
            # If the odoo company record is present in hubspot company,
            # take the corresponding hubspot record.
            if rec.hs_object_id in hubspot_company_list:
                hubspot_company_dict = {h.id: h for h in hubspot_company}
                hub_record = hubspot_company_dict.get(rec.hs_object_id, None)
                # If the hubspot record is recently modified then update
                # odoo record based on that.
                if hub_record.updated_at.astimezone(timezone.utc).replace(
                        tzinfo=None) > rec.write_date:
                    data_to_update = {
                        'name': hub_record.properties['name'],
                        'website': hub_record.properties['domain'],
                        'company_details': hub_record.properties['description'],
                        'phone': hub_record.properties['phone'],
                        'city': hub_record.properties['city'],
                        'state_id': state_dict.get(str(hub_record.properties[
                                                           'state']), None),
                        'country_id': country_dict.get(
                            str(hub_record.properties['country']), None),
                        'zip': hub_record.properties['zip'],
                    }
                    update_success += 1
                    rec.write(data_to_update)
        self.odoo_company_last_updated = datetime.now()
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.odoo_company_last_updated,
                'res_model_id': self.env.ref('base.model_res_company').id,
                'sync_mode': 'odoo_updated',
                'state': 'success',
                'count': update_success,
            })
        # Returns updated count.
        return update_success

    def action_export_deals(self):
        """ Method for exporting deals from Odoo to HubSpot """
        api_client = HubSpot(access_token=self.access_key)
        odoo_deals = self.env['crm.lead'].search([])
        hubspot_deals = []
        success_count = 0
        # Fetch all existing HubSpot deals
        existing_deals = api_client.crm.deals.get_all()
        for rec in existing_deals:
            hubspot_deals.append(rec.properties['hs_object_id'])
        # Create a mapping of Odoo stage names to HubSpot stage IDs
        stage_mapping = {
            'New': 'appointmentscheduled',
            'Qualified': 'qualifiedtobuy',
            'Proposition': 'presentationscheduled',
            'Won': 'closedwon',
            'Lost': 'closedlost',
        }
        priority_mapping = {
            '1': 'low',
            '2': 'medium',
            '3': 'high',
        }
        type_mapping = {
            'lead' : 'newbusiness',
            'opportunity':'existingbusiness'
        }
        # Export each Odoo deal to HubSpot if it doesn't already exist there
        for rec in odoo_deals:
            # If the deal present in Odoo is not available in HubSpot, create it via API call
            if rec.hs_object_id not in hubspot_deals:
                # Get the correct HubSpot owner ID
                # hubspot_owner_id = owner_mapping.get(rec.user_id.email, None)
                # Get the correct HubSpot deal stage ID
                hubspot_stage_id = stage_mapping.get(rec.stage_id.name, None)
                priority = priority_mapping.get(rec.priority, None)
                dealtype = type_mapping.get(rec.type, None)
                closedate = ''
                if rec.date_deadline:
                    closedate = datetime.combine(rec.date_deadline,
                                                 datetime.min.time()).astimezone(
                        pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                properties = {
                    "dealname": rec.name,
                    "amount": rec.expected_revenue if rec.expected_revenue else None,
                    "closedate": closedate,
                    "dealstage": hubspot_stage_id,
                    "hs_priority": priority,
                    'dealtype': dealtype,
                }
                # API call to create deals in HubSpot
                api_response = api_client.crm.deals.basic_api.create(
                    simple_public_object_input_for_create=
                    SimplePublicObjectInput(properties))
                # If the record is created in HubSpot, store the unique HubSpot ID in the deal record in Odoo too
                if api_response:
                    rec.write({
                        'hs_object_id': api_response.id,
                        'sync_mode': 'export'
                    })
                success_count += 1
        self.deals_last_exported = datetime.now()
        # If there is any record exported then creates history record
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.deals_last_exported,
                'res_model_id': self.env.ref('crm.model_crm_lead').id,
                'sync_mode': 'export',
                'state': 'success',
                'count': success_count,
            })
        # Returns the exported coun
        return success_count

    def action_import_deals(self):
    # Mapping of HubSpot priority values to Odoo priority values
        priority_mapping = {
            'low': '1',
            'medium': '2',
            'high': '3',
        }
        type_mapping = {
            'newbusiness':'lead',
            'existingbusiness':'opportunity',
        }
        # Needed fields to fetch from HubSpot.
        needed_fields = [
            "dealname", "amount", "closedate", "hs_priority",
            "dealtype", "hs_object_id",
        ]
        api_client = HubSpot(access_token=self.access_key)
        odoo_deals = self.env['crm.lead'].search([]).mapped('hs_object_id')
        hubspot_deals = api_client.crm.deals.get_all(properties=needed_fields)
        deals_to_create = []
        success_count = 0
        for rec in hubspot_deals:
            # If hubspot record not present in Odoo, create the record.
            if rec.properties['hs_object_id'] not in odoo_deals:
                # Map HubSpot priority value to Odoo priority value
                priority = priority_mapping.get(rec.properties['hs_priority'])
                type = type_mapping.get(rec.properties['dealtype'])
                deals_to_create.append({
                    'name': rec.properties['dealname'] or 'Lead',
                    'expected_revenue': rec.properties['amount'],
                    'date_deadline': rec.properties['closedate'],
                    'priority': priority,
                    'type': 'lead',
                    'hs_object_id': rec.properties['hs_object_id'],
                    'sync_mode': 'import',
                })
                success_count += 1
        # Create deals in Odoo
        if deals_to_create:
            self.env['crm.lead'].sudo().create(deals_to_create)
        self.deals_last_imported = datetime.now()
        # If created any records, create history for it.
        if success_count > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.deals_last_imported,
                'res_model_id': self.env.ref('crm.model_crm_lead').id,
                'sync_mode': 'import',
                'state': 'success',
                'count': success_count,
            })
        # Return the count of created records
        return success_count


    def action_update_hub_deals(self):
        """ Method for updating HubSpot record based on Odoo record. """

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        api_client = HubSpot(access_token=self.access_key)
        odoo_deals = self.env['crm.lead'].search([])
        odoo_deal_list = odoo_deals.mapped('hs_object_id')
        hubspot_deals = api_client.crm.deals.get_all()
        update_success = 0
        # Create mappings similar to action_export_deals method
        stage_mapping = {
            'New': 'appointmentscheduled',
            'Qualified': 'qualifiedtobuy',
            'Proposition': 'presentationscheduled',
            'Won': 'closedwon',
            'Lost': 'closedlost',
            # Add other mappings as necessary
        }
        priority_mapping = {
            '1': 'low',
            '2': 'medium',
            '3': 'high',
        }
        type_mapping = {
            'lead': 'newbusiness',
            'opportunity': 'existingbusiness'
        }
        # Split data_to_update into batches of maximum 100 records each
        for batch_data in chunks(hubspot_deals, 100):
            batch_update_success = 0
            batch_api_data = []
            for rec in batch_data:
                # If hubspot record present in odoo records then take the corresponding odoo record.
                if rec.properties['hs_object_id'] in odoo_deal_list:
                    odoo_record = odoo_deals.filtered(
                        lambda x: x.hs_object_id == rec.properties[
                            'hs_object_id'])
                    # If the odoo record is recently modified then update hubspot record based on that.
                    if odoo_record.write_date > rec.updated_at.astimezone(
                            timezone.utc).replace(tzinfo=None):
                        # Prepare data for update
                        closedate = ''
                        if odoo_record.date_deadline:
                            closedate = datetime.combine(
                                odoo_record.date_deadline,
                                datetime.min.time()).astimezone(
                                pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                        # Map Odoo fields to HubSpot fields
                        hubspot_stage_id = stage_mapping.get(
                            odoo_record.stage_id.name, None)
                        priority = priority_mapping.get(odoo_record.priority,
                                                        None)
                        dealtype = type_mapping.get(odoo_record.type, None)
                        batch_api_data.append({
                            'id': rec.properties['hs_object_id'],
                            'properties': {
                                "dealname": odoo_record.name,
                                "amount": odoo_record.expected_revenue if odoo_record.expected_revenue else None,
                                "closedate": closedate,
                                "dealstage": hubspot_stage_id,
                                "hs_priority": priority,
                                'dealtype': dealtype,
                            }
                        })
                        batch_update_success += 1
            # Batch update HubSpot deals
            if batch_api_data:
                api_client.crm.deals.batch_api.update(
                    batch_input_simple_public_object_batch_input=
                    BatchInputSimplePublicObjectBatchInput(batch_api_data))
            update_success += batch_update_success
        self.hub_deal_last_updated = datetime.now()
        # Create history record when any deal is updated.
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.hub_deal_last_updated,
                'res_model_id': self.env.ref('crm.model_crm_lead').id,
                'sync_mode': 'hub_updated',
                'state': 'success',
                'count': update_success,
            })
        # Returns the updated count.
        return update_success

    def action_update_odoo_deals(self):
        """ Method to update Odoo leads based on HubSpot records. """
        # Mapping of HubSpot priority values to Odoo priority values
        priority_mapping = {
            'low': '1',
            'medium': '2',
            'high': '3',
        }
        type_mapping = {
            'newbusiness': 'lead',
            'existingbusiness': 'opportunity',
        }
        # Needed fields to fetch from HubSpot
        needed_fields = ["dealname", "hs_object_id", "amount", "closedate",
                         "hs_priority", "dealtype"]
        api_client = HubSpot(access_token=self.access_key)
        odoo_deals = self.env['crm.lead'].search([])
        hubspot_deals = api_client.crm.deals.get_all(properties=needed_fields)
        hubspot_deal_list = {rec.properties['hs_object_id']: rec for rec in
                             hubspot_deals}
        update_success = 0
        for rec in odoo_deals:
            # If Odoo record present in HubSpot records, take the HubSpot record
            if rec.hs_object_id in hubspot_deal_list:
                hub_record = hubspot_deal_list[rec.hs_object_id]
                # If the HubSpot record is recently modified, update Odoo record based on that
                if hub_record.updated_at.astimezone(timezone.utc).replace(
                        tzinfo=None) > rec.write_date:
                    # Map HubSpot priority value to Odoo priority value
                    priority = priority_mapping.get(
                        hub_record.properties['hs_priority'])
                    type = type_mapping.get(hub_record.properties['dealtype'])
                    data_to_update = {
                        'name': hub_record.properties['dealname'] or 'Lead',
                        'expected_revenue': hub_record.properties['amount'],
                        'date_deadline': hub_record.properties['closedate'],
                        'priority': priority,
                        'type': type,
                    }
                    rec.write(data_to_update)
                    update_success += 1
        self.odoo_deal_last_updated = datetime.now()
        # Create history record based on updated records count
        if update_success > 0:
            self.env['hubspot.sync.history'].sudo().create({
                'date': self.odoo_deal_last_updated,
                'res_model_id': self.env.ref('crm.model_crm_lead').id,
                'sync_mode': 'odoo_updated',
                'state': 'success',
                'count': update_success,
            })
        # Return the updated count
        return update_success
