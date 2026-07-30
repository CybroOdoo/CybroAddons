# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo.exceptions import UserError


def _get_mailchimp_client(api_key):
    """Helper to import mailchimp_marketing and return a configured Client.
    Raises UserError with a friendly message if the library is not installed."""
    try:
        import mailchimp_marketing as MailchimpMarketing
        from mailchimp_marketing import Client
        from mailchimp_marketing.api_client import ApiClientError
    except ImportError:
        raise UserError(_(
            "This feature requires additional setup. "
            "Please contact your system administrator."
        ))
    client = Client()
    client.set_config({
        "api_key": api_key,
        "server": api_key.split('-')[1]
    })
    return client, MailchimpMarketing, ApiClientError


class MailchimpOperations(models.TransientModel):
    """
       Mailchimp Operation for importing and exporting data between
       Odoo and Mailchimp
    """
    _name = 'mailchimp.operations'
    _description = 'Import and Export Operations'

    mailchimp_account_ids = fields.Many2many('mailchimp.account',
                                             required=True,
                                             string="Mailchimp Accounts",
                                             help="Connect to MailChimp Account")
    is_import_list = fields.Boolean(string="Import List/Audiences",
                                    help="Importing Mailchimp Audiences")
    is_import_template = fields.Boolean(string="Import Template",
                                        help="Importing Mailchimp Template")
    is_import_campaigns = fields.Boolean(string="Import Campaigns",
                                         help="Importing Mailchimp Campaigns")
    is_export_list = fields.Boolean(string="Export List/Audiences",
                                    help="Exporting List and Audiences from "
                                         "Odoo to Mailchimp")
    is_export_template = fields.Boolean(string="Export Template",
                                        help="Exporting templates from "
                                             "Odoo to Mailchimp")

    def action_import(self):
        """Method which calls methods for importing list or audiences, importing
         templates and importing of campaigns from mailchimp."""
        if self.is_import_list:
            self.import_list()
        if self.is_import_template:
            self.import_templates()
        if self.is_import_campaigns:
            self.import_campaigns()

    def import_list(self):
        """ Method to import list or audiences from mailchimp."""
        client, _, _ = _get_mailchimp_client(self.mailchimp_account_ids.api_key)
        response = client.lists.get_all_lists()
        for list_info in response['lists']:
            existing_list = self.env['mailchimp.mailing.list'].search(
                [('name', '=', list_info['name'])])
            if existing_list:
                continue
            country = self.env['res.country'].search(
                [('name', '=', list_info['contact']['country'])], limit=1)
            language = self.env['res.lang'].search(
                [('name', '=', list_info['campaign_defaults']['language'])],
                limit=1)
            state = self.env['res.country.state'].search(
                [('name', '=', list_info['contact']['state'])], limit=1)
            if not state:
                state = self.env['res.country.state'].create({
                    'name': list_info['contact']['state'],
                    'country_id': country.id,
                    'code': list_info['contact']['state']
                })
            vals = {
                'name': list_info['name'],
                'create_date': list_info['date_created'],
                'permission_reminder': list_info['permission_reminder'],
                'has_email_type': list_info.get('email_type_option', False),
                'address': list_info['contact']['address1'],
                'city': list_info['contact']['city'],
                'zip': list_info['contact']['zip'],
                'state_id': state.id,
                'country_id': country.id,
                'from_name': list_info['campaign_defaults']['from_name'],
                'from_email': list_info['campaign_defaults']['from_email'],
                'subject': list_info['campaign_defaults']['subject'],
                'list_rating': list_info['list_rating'],
                'lang_id': language.id,
                'member_count': list_info['stats']['member_count'],
                'unsubscribe_count': list_info['stats']['unsubscribe_count'],
                'campaign_count': list_info['stats']['campaign_count'],
                'click_rate': list_info['stats']['click_rate'],
            }
            self.env['mailchimp.mailing.list'].create(vals)
            existing_mailing_list = self.env['mailing.list'].search(
                [('name', '=', list_info['name'])])
            if not existing_mailing_list:
                mailing_list = self.env['mailing.list'].create({
                    'name': list_info['name'],
                    'is_public': True,
                    'create_date': list_info['date_created'],
                })
                self.env['mailing.contact'].create({
                    'name': list_info['campaign_defaults']['from_name'],
                    'email': list_info['campaign_defaults']['from_email'],
                    'country_id': country.id,
                    'list_ids': mailing_list
                })

    def import_templates(self):
        """ Method to import templates from mailchimp."""
        client, _, _ = _get_mailchimp_client(self.mailchimp_account_ids.api_key)
        response = client.templates.list()
        for template_info in response['templates']:
            existing_templates = self.env['mailchimp.template'].search(
                [('name', '=', template_info['name'])])
            if not existing_templates:
                vals = {
                    'name': template_info['name'],
                    'is_active': template_info['active'],
                    'type': template_info['type'],
                    'is_drag_drop': template_info['drag_and_drop'],
                    'share_url': template_info['thumbnail']
                }
                self.env['mailchimp.template'].create(vals)

    def import_campaigns(self):
        """Method to import campaigns from mailchimp."""
        client, _, _ = _get_mailchimp_client(self.mailchimp_account_ids.api_key)
        response = client.campaigns.list()
        for list_info in response['campaigns']:
            existing_campaign = self.env['utm.campaign'].search(
                [('title', '=', list_info['settings']['title'])], limit=1)
            if not existing_campaign:
                vals = {
                    'name': list_info['settings']['title'],
                    'create_date': list_info['create_time'],
                    'title': list_info['settings']['title'],
                    'mailing_mail_count': list_info['emails_sent'],
                }
                self.env['utm.campaign'].create(vals)

    def action_export(self):
        """Method which calls methods for exporting mailing lists to Mailchimp."""
        if self.is_export_list:
            self.export_list()

    def export_list(self):
        """Export mailing lists from Odoo to Mailchimp."""
        client, _, ApiClientError = _get_mailchimp_client(
            self.mailchimp_account_ids.api_key
        )
        company = self.env.company

        if not all([
            company.email,
            company.street,
            company.city,
            company.zip,
            company.country_id,
        ]):
            raise UserError(_(
                "Please fill in all company details before exporting."
            ))

        try:
            existing_audiences = client.lists.get_all_lists()

            if existing_audiences.get("lists"):
                audience_id = existing_audiences["lists"][0]["id"]
            else:
                new_list = client.lists.create_list({
                    "permission_reminder": (
                        "You are receiving this email because you opted in via our website."
                    ),
                    "name": "Odoo Audience",
                    "email_type_option": True,
                    "campaign_defaults": {
                        "from_name": company.name,
                        "from_email": company.email,
                        "subject": "",
                        "language": "en",
                    },
                    "contact": {
                        "company": company.name,
                        "address1": company.street,
                        "city": company.city,
                        "state": company.state_id.name if company.state_id else "",
                        "zip": company.zip,
                        "country": company.country_id.code,
                    },
                })
                audience_id = new_list["id"]

            mailing_lists = self.env["mailing.list"].search([])

            for mailing_list in mailing_lists:
                for contact in mailing_list.contact_ids:

                    if not contact.email:
                        continue

                    member_info = {
                        "email_address": contact.email,
                        "status": "subscribed",
                        "merge_fields": {
                            "FNAME": contact.name or "",
                        },
                    }

                    try:
                        client.lists.add_list_member(
                            audience_id,
                            member_info,
                        )

                    except ApiClientError as e:
                        raise UserError(e.text)

                    except Exception as e:
                        raise UserError(str(e))

        except ApiClientError as e:
            raise UserError(e.text)

        except Exception as e:
            raise UserError(str(e))

    def sync_mailchimp_list(self):
        """Scheduled action to automatically sync audiences,templates and
        members on mailchimp."""
        if self.mailchimp_account_ids.is_auto_sync:
            self.import_list()
            self.import_templates()
            self.import_campaigns()
            self.export_list()