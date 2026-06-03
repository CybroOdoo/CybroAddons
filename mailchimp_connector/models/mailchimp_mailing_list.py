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

    name = fields.Char(string="Name",
                       help="Name of list/audiences")
    is_synced = fields.Boolean(string="Is synchronized",
                               help="Indicates whether the audience is synced with Mailchimp"
                               )
    audience_id = fields.Char(string="Audience ID",
                              help="Audience ID set on the mailchimp")
    mailchimp_account_id = fields.Many2one('mailchimp.account',
                                           help="Related Mailchimp account for this audience",
                                           string="Mailchimp Account")
    list_rating = fields.Integer(string="List Rating",
                                 help="Rating of the Mailchimp audience")
    member_count = fields.Integer(string="Contacts",
                                  help="Total number of contacts in the audience")
    list_rating_display = fields.Integer(string="List Rating",
                                         help="Computed display value for list rating",
                                         compute='_compute_list_rating_display')
    member_count_display = fields.Integer(string="Contacts",
                                          compute="_compute_member_count_display",
                                          help="Computed display value for contact count")
    mailchimp_list_id = fields.Char(string="Mailchimp List id",
                                    help="Internal Mailchimp list identifier")
    email_type_option = fields.Boolean(string="Email type option",
                                       help="Indicates whether email type options are enabled")
    from_name = fields.Char(string="From name", required=True,
                            help="Default sender name for campaigns")
    from_email = fields.Char(string="From email", required=True,
                             help="Default sender email address for campaigns")
    subject = fields.Char(string="Subject", required=True,
                          help="Default subject line for campaigns")
    lang_id = fields.Many2one("res.lang", string="Language",
                              help="Preferred language for the audience")
    company_id = fields.Many2one("res.company", string="Company",
                                 default=(lambda self: self.env.company.id),
                                 help="Company associated with this audience")
    address = fields.Char(string="Address ", required=True,
                          help="Company or sender address")
    city = fields.Char(string="City", required=True,
                       help="City of the address")
    permission_reminder = fields.Text(string="Permission Reminder",
                                      required=True,
                                      help="Reminder message explaining why contacts receive emails")
    zip = fields.Char(string="Zip", required=True,
                      help="ZIP or postal code of the address")
    state_id = fields.Many2one("res.country.state",
                               domain="[('country_id', '=?', country_id)]",
                               help="State corresponding to the selected country")
    country_id = fields.Many2one("res.country",
                                 help="Country of the address")
    is_sync_success = fields.Boolean(string="Is Synced",
                                     help="Indicates whether the last synchronization was successful")
    unsubscribe_count = fields.Integer(string="Unsubscribed Count",
                                       help="Number of unsubscribed contacts")
    campaign_count = fields.Integer(string="Campaign Count",
                                    help="Number of campaigns associated with this audience")
    click_rate = fields.Integer(string="Click Rate",
                                help="Click rate percentage of campaigns"
                                )
    unsubscribe_count_display = fields.Integer(string="Unsubscribed Count",
                                               compute="_compute_unsubscribe_count_display",
                                               help="Computed display value for unsubscribed contacts")
    campaign_count_display = fields.Integer(string="Campaign Count",
                                            compute="_compute_campaign_count_display",
                                            help="Computed display value for campaign count")
    click_rate_display = fields.Integer(string="Click Rate",
                                        compute="_compute_click_rate_display",
                                        help="Computed display value for click rate")
    state = fields.Selection(
        [('not_connect ', 'Not Connected'), ('connected', 'Connected')],
        string="Status",
        help="Connection status of the Mailchimp audience")

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
