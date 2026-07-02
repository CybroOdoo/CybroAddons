# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class MailchimpMailingList(models.Model):
    """This model includes records of list/audience in mailchimp"""
    _name = 'mailchimp.mailing.list'
    _description = 'List/Audiences'

    name = fields.Char(
        string="Name",
        help="Name of list/audiences"
    )
    is_synced = fields.Boolean(
        string="Is synchronized",
        help="Whether the list is synced with Mailchimp."
    )
    audience_id = fields.Char(
        string="Audience ID",
        help="The Mailchimp Audience ID."
    )
    mailchimp_account_id = fields.Many2one(
        'mailchimp.account',
        string="Mailchimp Account",
        help="Mailchimp account ID associated with the list."
    )
    list_rating = fields.Integer(
        string="List Rating",
        help="The rating of the Mailchimp list."
    )
    member_count = fields.Integer(
        string="Contacts",
        help="Total number of contacts in the list."
    )
    list_rating_display = fields.Integer(
        string="List Rating",
        compute='_compute_list_rating_display',
        help="Computed rating of the list."
    )
    member_count_display = fields.Integer(
        string="Contacts",
        compute="_compute_member_count_display",
        help="Computed contact count in the list."
    )
    mailchimp_list_id = fields.Char(
        string="Mailchimp List ID",
        help="Mailchimp ID for the list."
    )
    email_type_option = fields.Boolean(
        string="Email Type Option",
        help="Indicates if different email types are supported."
    )
    from_name = fields.Char(
        string="From Name",
        required=True,
        help="Name displayed in the 'From' field of emails."
    )
    from_email = fields.Char(
        string="From Email",
        required=True,
        help="Email address displayed in the 'From' field of emails."
    )
    subject = fields.Char(
        string="Subject",
        required=True,
        help="Subject line of the email campaigns."
    )
    lang_id = fields.Many2one(
        "res.lang",
        string="Language",
        help="Language preference for the list."
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company.id,
        help="Company associated with the list."
    )
    address = fields.Char(
        string="Address",
        required=True,
        help="Physical address of the company."
    )
    city = fields.Char(
        string="City",
        required=True,
        help="City of the company's address."
    )
    permission_reminder = fields.Text(
        string="Permission Reminder",
        required=True,
        help="Message to remind users of their permission."
    )
    zip = fields.Char(
        string="Zip",
        required=True,
        help="Zip code of the company's address."
    )
    state_id = fields.Many2one(
        "res.country.state",
        domain="[('country_id', '=?', country_id)]",
        help="State of the company's address."
    )
    country_id = fields.Many2one(
        "res.country",
        help="Country of the company's address."
    )
    is_sync_success = fields.Boolean(
        string="Is Sync Successful",
        help="Whether synchronization with Mailchimp was successful."
    )
    unsubscribe_count = fields.Integer(
        string="Unsubscribed Count",
        help="Number of contacts who have unsubscribed."
    )
    campaign_count = fields.Integer(
        string="Campaign Count",
        help="Number of campaigns associated with the list."
    )
    click_rate = fields.Integer(
        string="Click Rate",
        help="Rate of clicks within the list's campaigns."
    )
    unsubscribe_count_display = fields.Integer(
        string="Unsubscribed Count",
        compute="_compute_unsubscribe_count_display",
        help="Computed unsubscribed count."
    )
    campaign_count_display = fields.Integer(
        string="Campaign Count",
        compute="_compute_campaign_count_display",
        help="Computed campaign count."
    )
    click_rate_display = fields.Integer(
        string="Click Rate",
        compute="_compute_click_rate_display",
        help="Computed click rate."
    )
    state = fields.Selection(
        [('not_connected', 'Not Connected'), ('connected', 'Connected')],
        string="Status",
        help="Connection status with Mailchimp."
    )

    @api.depends('unsubscribe_count')
    def _compute_unsubscribe_count_display(self):
        """
           Computing the unsubscribe count while importing Mailing list from
           mailchimp to Odoo.
        """
        for record in self:
            record.unsubscribe_count_display = record.unsubscribe_count

    @api.depends('campaign_count')
    def _compute_campaign_count_display(self):
        """
            Computing the compaign count while importing Mailing list from
            mailchimp to Odoo.
        """
        for record in self:
            record.campaign_count_display = record.campaign_count

    @api.depends('list_rating')
    def _compute_list_rating_display(self):
        """
          Computing the list rating count while importing Mailing list from
          mailchimp to Odoo.
        """
        for record in self:
            record.list_rating_display = record.list_rating

    @api.depends('member_count')
    def _compute_member_count_display(self):
        """
            Computing the member count while importing Mailing list from
            mailchimp to Odoo.
        """
        for record in self:
            record.member_count_display = record.member_count

    @api.depends('click_rate')
    def _compute_click_rate_display(self):
        """
           Computing the click rate count while importing Mailing list from
           mailchimp to Odoo.
        """
        for record in self:
            record.click_rate_display = record.click_rate

    def action_import(self):
        """
           Importing contact list data
        """
        return False
