# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Hridhya D (<https://www.cybrosys.com>)
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
from datetime import datetime
from werkzeug import urls
from odoo import api, fields, models, _


class VisaApproval(models.Model):
    """The class VisaApproval is for applying the Visa"""
    _name = 'visa.approval'
    _description = 'Visa Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Approval No", readonly=True,
                       default='New', help="Approval No")
    application_date = fields.Date(default=datetime.today(),
                                   string="Application Date",
                                   help="Date of Applying Visa")
    visa_application_no_id = fields.Many2one('visa.application',
                                             string="Visa Application No",
                                             help="Visa application number"
                                                  " of employee")
    expire_date = fields.Date(string="Expire Date",
                              help="Expiry Date of the Visa")
    is_expired = fields.Boolean(string='Is Expired',
                                compute='_compute_is_expired',
                                search='_search_is_expired',
                                help="If enabled, the Visa is expired")
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'), ('approved', 'Approved'),
         ('expired', 'Expired'),
         ('reject', 'Rejected')], default='draft',
        help="State of visa approval",
        string='State of approval')
    employee_id = fields.Many2one("hr.employee", string="Employee Name",
                                  help="Name of the Employee")
    visa_type = fields.Selection([
        ('tourist', 'Tourist'),
        ('immigration', 'Immigration'),
        ('student', 'Student'),
        ('work', 'Work'),
        ('other', 'Other')], string="Visa Type", help="Type of visa")
    nationality_id = fields.Many2one(related="employee_id.country_id",
                                     string="Nationality",
                                     help="Nationality of the employee")
    department_id = fields.Many2one(related="employee_id.department_id",
                                    string="Department",
                                    help="Department of the employee")
    profession = fields.Char(related="employee_id.job_title",
                             string="Profession",
                             help="Profession of the employee")
    passport = fields.Char(related="employee_id.passport_id",
                           string="Passport No",
                           help="Passport of the employee")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')], related="employee_id.gender",
        help="Gender of the employee", string="Gender of the employee")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="If set, corresponding record are shown "
                                      "for this specific company")

    @api.model
    def update_state(self):
        """This function updates the state to expired if the visa is expired"""
        for rec in self.search([('expire_date', '<', fields.date.today())]):
            rec.write({'state': 'expired'})

    @api.model
    def create(self, vals):
        """This function is used to generate sequence number for visa
        approval"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'visa.management') or 'New'
            result = super(VisaApproval, self).create(vals)
            return result

    def action_visa_approve(self):
        """This function is used to approve the visa"""
        self.state = 'approved'
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        page_url = urls.url_join(base_url,
                                 'web#id=%(id)s&model=visa.approval&view_type=form'
                                 % {'id': self.id})
        mail_content = _('Hi %s,<br>'
                         '<div style = "text-align: left; margin-top: 16px;">'
                         'Your VISA Application have been approved.<br/>'
                         'You can check further details by clicking on the '
                         'button below:<br/>'
                         '<a href = "%s"'
                         'style = "padding: 5px 10px; font-size: 12px; '
                         'line-height: 18px; color: #FFFFFF; '
                         'border-color:#875A7B;text-decoration: none; '
                         'display: inline-block; '
                         'margin-bottom: 0px; font-weight: 400;'
                         'text-align: left; vertical-align: middle; '
                         'cursor: pointer; white-space: nowrap;'
                         ' background-image: none; '
                         'background-color: #875A7B; border: 1px solid #875A7B;'
                         ' border-radius:3px;">'
                         'View</a></div>'
                         ) % (self.employee_id.name, page_url)
        email_to = self.employee_id.work_email
        main_content = {
            'subject': _('Visa Approved'),
            'body_html': mail_content,
            'email_to': email_to
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()

    def action_visa_submit(self):
        """This function is used to submit the visa application and it sends a
        mail to the mail given in the company
        provided in the address_id in the corresponding employee"""
        self.state = 'submit'
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        page_url = urls.url_join(base_url,
                                 'web#id=%(id)s&model=visa.approval&view_type=form'
                                 % {'id': self.id})
        mail_content = _('Hi,<br>'
                         '<div style = "margin-top: 16px;">'
                         'The details of visa application and further details '
                         'can be viewed by '
                         'clicking on the button below:<br/>'
                         '<a href = "%s"'
                         'style = "margin-top: 16px; padding: 5px 10px; '
                         'font-size: 12px; line-height: 18px; color: #FFFFFF; '
                         'border-color:#875A7B;text-decoration: none; '
                         'display: inline-block; '
                         'margin-bottom: 0px; font-weight: 400;'
                         'text-align: center; vertical-align: middle; '
                         'cursor: pointer; white-space: nowrap; '
                         'background-image: none; '
                         'background-color: #875A7B; border: 1px solid #875A7B;'
                         ' border-radius:3px;">'
                         'View</a></div>'
                         ) % (page_url)
        email_to = self.employee_id.address_id.email
        main_content = {
            'subject': _('Visa Application'),
            'body_html': mail_content,
            'email_to': email_to
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()

    def action_renew(self):
        """This function changes the state back to draft state"""
        self.write({'state': 'draft'})

    def action_reject(self):
        """This function is used to reject the visa application and it sends
         a mail to the employee"""
        self.state = 'reject'
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        Urls = urls.url_join(base_url,
                             'web#id=%(id)s&model=visa.approval&view_type=form'
                             % {'id': self.id})
        mail_content = _('Hi %s,<br>'
                         '<div style = "text-align: center; margin-top: 16px;">'
                         'Your VISA Application have been rejected.<br/>'
                         'You can check further details by clicking on the '
                         'button below:<br/>'
                         '<a href = "%s"'
                         'style = "padding: 5px 10px; font-size: 12px;'
                         ' line-height: 18px; color: #FFFFFF; '
                         'border-color:#875A7B;text-decoration: none; '
                         'display: inline-block; '
                         'margin-bottom: 0px; font-weight: 400;'
                         'text-align: center; vertical-align: middle; '
                         'cursor: pointer; white-space: nowrap;'
                         ' background-image: none; '
                         'background-color: #875A7B; border: 1px solid #875A7B;'
                         ' border-radius:3px;">'
                         'View</a></div>'
                         ) % \
                       (self.employee_id.name, Urls)
        email_to = self.employee_id.work_email
        main_content = {
            'subject': _('Visa Rejected'),
            'body_html': mail_content,
            'email_to': email_to
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()

    def _compute_is_expired(self):
        """This function is used to compute the is_expired field"""
        now = fields.Datetime.now()
        for rec in self:
            rec.is_expired = now.date() > rec.expire_date

    def _search_is_expired(self):
        """This function is used to search the is_expired field"""
        now = fields.Datetime.now()
        ids = self.env['visa.approval']._search([('expire_date', '<', now)])
        return [('id', 'in', ids)]
