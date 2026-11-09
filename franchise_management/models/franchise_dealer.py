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
"""Franchise Dealer Model"""
import base64
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError


class FranchiseDealer(models.Model):
    """Franchise Dealer Model."""
    _name = "franchise.dealer"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin',
                'utm.mixin']
    _description = "Dealers"
    _rec_name = "dealer_name"

    serial_no = fields.Char(string="Sl No", readonly=True, copy=False,
                            default='New', help='Record serial no')
    dealer_name = fields.Char(string='Franchisee Name', help='Franchisee Name', required=True)
    dealer_user_id = fields.Many2one('res.users', string="user",
                                     help='User')
    street = fields.Char(help='Street1 Name')
    street2 = fields.Char(help='Street2 Name')
    zip = fields.Char(change_default=True, string='Zip code',
                      help='Franchisee Zip code')
    city = fields.Char(help='City Name')
    state_id = fields.Many2one("res.country.state",
                               ondelete='restrict', help='Franchisee state',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country',
                                 help='Franchisee Country',
                                 ondelete='restrict')
    country_code = fields.Char(related='country_id.code',
                               string="Country Code",
                               help='Franchisee Country code')
    dealer_qualification = fields.Char(string='Qualification',
                                       help='Franchise Qualification')
    dealer_occupation = fields.Char(string='Current Occupation',
                                    help='Franchisee Occupation')
    dealer_phone = fields.Char(string='Phone', help='Franchise Phone')
    dealer_mobile = fields.Char(string='Mobile', help='Mobile number')
    dealer_mail = fields.Char(string='Email', required=True,
                              help='Franchise email')
    dealer_website = fields.Char(string='Website', help='Franchisee Website')
    advertisement = fields.Selection(
        selection=[('advertisement', 'Advertisement'),
                   ('area_sales_manager', 'Area Sales Manager'),
                   ('regional_manager', 'Regional Manager'),
                   ('others', 'Others')],
        help='Dealer Vacancy Known Through',
        default='advertisement')
    business_city = fields.Char(string='City Interested in',
                                help='City Interested to Franchise')
    business_country = fields.Many2one('res.country',
                                       string='Country Interested in',
                                       help='Country Interested to Franchise',
                                       ondelete='restrict')
    experience = fields.Text(string='Experience in this Business',
                             help='Experience in this Business')
    earnings = fields.Char(string='Last year Earnings',
                           help='Last year earnings in the business')
    business_experience_ids = fields.One2many('business.experience',
                                              'experience_id',
                                              string='Experience',
                                              help='Business Experience')
    site_location = fields.Char(help='Business Site location')
    site_type = fields.Selection(
        selection=[('owned', 'Owned'), ('rented', 'Rented'),
                   ('leased', 'Leased'), ('others', 'Others')],
        default='owned', help='Business Site Type')
    site_area = fields.Float(string='Total Area(in sq/ft)',
                             help='Total site area in sq ft')
    investment_from = fields.Float(string='From', help='Investment From')
    investment_to = fields.Float(string='To', help='Investment To')
    company_id = fields.Many2one('res.company',
                                 help='Company Name',
                                 change_default=True,
                                 default=lambda self: self.env.company,
                                 required=False)
    user_id = fields.Many2one('res.users', string='Responsible',
                              help='Responsible User',
                              default=lambda self: self.env.user)
    url = fields.Char(string='url', help='url to website')
    feedback_url = fields.Char(string='Feedback url',
                               help='Feedback Url to feedback form')
    signature = fields.Image(copy=False, attachment=True,
                             help='Franchise Dealer Signature',
                             max_width=1024, max_height=1024)
    signed_by = fields.Char(copy=False,
                            help='Franchise Contract Signed By')
    signed_on = fields.Date(copy=False,
                            help='Franchise Contract Signed On')
    contract_renewal_date = fields.Date(string="Renewal Date", store=True,
                                        help='Contract Renewal Date',
                                        compute='_compute_renewal_date')
    priority = fields.Selection(
        selection=[('0', 'Low'), ('1', 'Medium'),
                   ('2', 'High'), ('3', 'Very High')],
        default='0', help='Prioritise the dealer',
        index=True, tracking=True)
    dealer_portal_user = fields.Many2one('res.users',
                                         string='Portal User Name',
                                         help='Dealer Portal User Name')
    monthly_target_amount = fields.Float(required=True,
                                         help='Franchise Monthly Target Amount')
    state = fields.Selection(
        selection=[('a_draft', 'Draft'), ('b_to_approve', 'To Approve'),
                   ('c_approve', 'Approved'), ('d_cancel', 'Rejected'),
                   ('e_contract', 'Contract Proposal'),
                   ('g_declined', 'Declined'),
                   ('f_signed', 'Contract Signed'),
                   ('h_feedback', 'Feedback Sent')
                   ],
        string='Status', help='Status', required=True, readonly=True,
        copy=False, tracking=True, default='a_draft')
    # contract
    contract_type_id = fields.Many2one('franchise.agreement',
                                       string='Agreement Type',
                                       required=True,
                                       help='Franchise Agreement Type')
    body_html = fields.Html(string='Body',
                            translate=True, prefetch=True, sanitize=False,
                            compute="_compute_body_html",
                            help='Franchise Agreement Body',
                            inverse="_inverse_contract", store=True)

    @api.constrains('monthly_target_amount')
    def _monthly_target_amount(self):
        """ Constraint to validate the number of featured blogs.
            Raises: ValidationError: If more than three blogs are added."""
        if self.monthly_target_amount == 0.00:
            raise UserError(self.env._('Please enter the monthly target amount.'))

    @api.depends('contract_type_id')
    def _compute_body_html(self):
        """Contract type computation function."""
        for rec in self:
            rec.body_html = rec.contract_type_id.agreement_body

    def _inverse_contract(self):
        """Inverse function to make the compute field editable"""
        self.body_html = self.body_html

    @api.depends('signed_on', 'contract_type_id.agreement_type')
    def _compute_renewal_date(self):
        """Franchise dealer contract renewal date computation function."""
        for record in self:
            record.contract_renewal_date = 0
            if record.signed_on:
                if record.contract_type_id.agreement_type == 'Yearly':
                    record.contract_renewal_date = (record.signed_on +
                                                    timedelta(days=365))
                if record.contract_type_id.agreement_type == 'Monthly':
                    record.contract_renewal_date = (record.signed_on +
                                                    timedelta(days=30))
            else:
                record.contract_renewal_date = 0

    # EXTENDS portal portal.mixin
    def _compute_access_url(self):
        """Compute url in portal mixin."""
        res = super()._compute_access_url()
        for move in self:
            move.access_url = '/my/franchise/%s' % (move.id)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Franchise dealer model sequence create method."""
        for vals in vals_list:
            if vals.get('serial_no', self.env._("New")) == self.env._("New"):
                vals['serial_no'] = self.env['ir.sequence'].next_by_code(
                    'franchise.dealer') or 'New'
            if vals.get('contract_type_id', False):
                vals['body_html'] = self.env['franchise.agreement'].browse(
                    int(vals['contract_type_id'])).agreement_body
        return super(FranchiseDealer, self).create(vals_list)

    def action_confirm(self):
        """Function of confirm button."""
        self.write({'state': "b_to_approve"})

    def action_approve(self):
        """Function of approve button."""
        self.write({'state': "c_approve"})

    def action_cancel(self):
        """Function of cancel button."""
        self.write({'state': "d_cancel"})

    def contract_signed(self):
        """Function of contract sign button."""
        self.write({'state': "f_signed"})

    def contract_declined(self):
        """Function of reject_sign button in website portal."""
        self.write({'state': "g_declined"})

    def action_send_contract(self):
        """Contract send on button function."""
        base_url = str(self.get_base_url()) + str("/@/my/franchise/") + str(
            self.id)
        self.url = base_url
        self.write({'state': "e_contract"})
        template = self.env.ref('franchise_management.contract_email_template')
        self.argument_function(template)
        return True

    def action_send_contract_renewal(self):
        """Contract renewal schedule action."""
        today_renewals = self.env['franchise.dealer'].search(
            [('contract_renewal_date', '=', datetime.today().date())])
        if today_renewals:
            for i in today_renewals:
                template = self.env.ref(
                    'franchise_management.contract_renewal_email_template')
                self.argument_function(template)
                return True

    def argument_function(self, template):
        """Contract send and renewal argument function."""
        current_dealer_order = self.env['franchise.dealer'].browse(self.id)
        email_values = {'email_to': current_dealer_order.dealer_mail, }
        form_data = {
            'data': current_dealer_order,
        }
        report_template_id = self.env.ref(
            'franchise_management.franchise_contract_report_action'
        )._render_qweb_pdf(
            'franchise_management.franchise_contract_report_action', self.id,
            data=form_data)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Dealership Contract",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        template.attachment_ids = [(6, 0, [data_id.id])]
        template.send_mail(self.id, email_values=email_values, force_send=True)
        template.attachment_ids = [(3, data_id.id)]
        self.message_post_with_source(
            template,
            attachment_ids=[data_id.id],
            subtype_xmlid='mail.mt_comment',
        )

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed
        Sales).:return: `mail.template` record or None if default template
        wasn't found"""
        return self.env.ref('franchise_management.portal_user_email_template',
                            raise_if_not_found=False)

    def _send_order_confirmation_mail(self):
        """Dealer request confirmation mail after signing the contract."""
        if not self:
            return
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        for record in self:
            mail_template = record._get_confirmation_template()
            if not mail_template:
                continue
            email_values = {'email_to': record.dealer_mail, }
            mail_template.send_mail(record.id, email_values=email_values, force_send=True)
            record.message_post_with_source(
                mail_template,
                subtype_xmlid='mail.mt_comment',
            )
    def create_portal_user(self):
        """After contract signed,the dealer created as portal user."""
        user = self.env['res.users'].create({
            'name': self.dealer_name,
            'login': self.dealer_mail,
            'email': self.dealer_mail,
            'phone': self.dealer_phone,
            'website': self.dealer_website,
            'password': 'franchise00129',
            'street': self.street,
            'zip': self.zip,
            'group_ids': [(4, self.env.ref('base.group_portal').id)]
        })
        self.dealer_portal_user = user.id
        return user

    def action_preview_dealer_order(self):
        """Dealer portal preview from backend."""
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.url,
        }

    def action_dealer_feedback(self):
        """Dealer sale feedback smart button to view feedback report
         of the product"""
        feedback_ids = self.env['dealer.sale'].search([
            ('dealer_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dealership feedback',
            'view_mode': 'list,form',
            'res_model': 'dealer.sale',
            'domain': [('id', 'in', feedback_ids)],
            'context': "{'create': False}"
        }

    def action_send_feedback(self):
        """Method to send franchise feedback"""
        base_url = str(self.get_base_url()) + str(
            "/@/feedback_report_menu?id=") + str(self.id)
        self.feedback_url = base_url
        current_dealer_order = self.env['franchise.dealer'].browse(self.id)
        email_values = {'email_to': current_dealer_order.dealer_mail, }
        template = self.env.ref('franchise_management.feedback_email_template')
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.message_post_with_source(
            template,
            subtype_xmlid='mail.mt_comment',
        )
        return True
