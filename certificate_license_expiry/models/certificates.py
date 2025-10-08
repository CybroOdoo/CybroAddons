# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Albin PJ (odoo@cybrosys.com)
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
###############################################################################
from random import randint
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Certificates(models.Model):
    """This will give all about certificates such as fields etc"""
    _name = 'certificates'
    _description = "Certificates"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection(
        selection=[('new', 'New'), ('active', 'Active'),
                   ('expired_soon', 'Expired Soon'), ('expired', 'Expired')],
        string="State", default='new', help="Sates of certificate")
    name = fields.Char(string='Name', required=True, help="Name of certificate")
    certificate_number = fields.Char(string="Certificate Number",
                                     readonly=True, copy=False,
                                     default='New', help="Sequence number")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  required=True, help="Name of the customer")
    certificates_types_id = fields.Many2one('certificates.types',
                                            string="Certificates Types",
                                            required=True, help="Type of the "
                                                                "certificate")
    start_date = fields.Date(string="Start Date", required=True,
                             default=fields.Date.today(), help="Certificate "
                                                               "start date")
    expire_date = fields.Date(string="Expire Date", help="Certificate expiry "
                                                         "date")
    issued_company_id = fields.Many2one('res.company', string="Issued By",
                                        required=True,
                                        help="Certificate issued by "
                                             "which company")
    certificates_tags_ids = fields.Many2many('certificates.tags', string="Tags",
                                             help="Tags of the certificate")
    project_id = fields.Many2one('project.project', string="Project",
                                 required=True,
                                 help="Project corresponding to the "
                                      "certificate")
    task_id = fields.Many2one('project.task', string="Task",
                              domain="[('project_id', '=', project_id)]",
                              required=True,
                              help="Task corresponding to the certificate")
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True,
                                 help="Product corresponding to the "
                                      "certificate")
    user_id = fields.Many2one('res.users', string="Responsible Person",
                              required=True,
                              default=lambda self: self.env.user,
                              help="Responsible user of the certificate")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True,
                                 help="Company corresponding to the "
                                      "certificate")
    expire_remainder_day = fields.Integer(string="Expire Reminder Day",
                                          help="Certificate expire remainder "
                                               "day")
    login_user_id = fields.Many2one('res.users', string='Login User',
                                    default=lambda self: self.env.user,
                                    readonly=True,
                                    help="ID of the logged in user")
    internal_notes = fields.Text(string="Internal Notes",
                                 help="Internal notes of the certificate")
    description = fields.Text(string="Description", required=True,
                              help="Description of the certificate")
    achievements = fields.Text(string="Achievements",
                               help="Achievements in the certificate")
    has_expired = fields.Boolean(string="Expired Certificate",
                                 help="Becomes True if the certificate "
                                      "has expired")

    @api.model
    def create(self, vals):
        """This is used to get the certificate number"""
        if vals.get('certificate_number', 'New') == 'New':
            vals['certificate_number'] = self.env['ir.sequence'].next_by_code(
                'certificates') or 'New'
        result = super(Certificates, self).create(vals)
        return result

    @api.constrains('start_date', 'expire_date')
    def _constrains_certificate_start_date_expire_date(self):
        """This will give validation at the time of expired date and start
        date have any problem"""
        if self.start_date and self.expire_date:
            if (self.start_date > self.expire_date or fields.Date.today() >
                    self.expire_date):
                raise ValidationError(_('Expire Date Is Not Valid'))

    def active_certificate(self):
        """It changes the state into active"""
        self.state = 'active'

    def action_active_certificate(self):
        """It returns the certificate tree view"""
        return {
            'name': 'Active',
            'view_mode': 'tree',
            'res_model': 'certificates',
            'type': 'ir.actions.act_window',
            'domain': [('state', '=', 'active')],
            'context': "{'create': False}"
        }

    def certificate_expiry_action(self):
        """This function is from scheduled action, it will send mail
        notification and change the state based on condition given below"""
        certificates = self.env['certificates'].search(
            [('has_expired', '=', False)])
        today = fields.Date.today()
        for rec in certificates:
            if today >= fields.Date.subtract(
                    rec.expire_date, days=rec.expire_remainder_day):
                rec.state = 'expired_soon'
            if today >= rec.expire_date and rec.state != 'expired':
                email_values = {
                    'email_cc': False,
                    'auto_delete': True,
                    'recipient_ids': [],
                    'partner_ids': [],
                    'scheduled_date': False,
                    'email_to': rec.customer_id.email
                }
                template = self.env.ref(
                    'certificate_license_expiry.email_template_certificate')
                template.send_mail(rec.id, force_send=True,
                                   email_values=email_values)
                rec.state = 'expired'
                rec.has_expired = True

    def action_create_certificate_pdf_report(self):
        """This is used to get pdf report and passes the values to template"""
        data = {
            'record_name': self.name,
            'record_certificate_number': self.certificate_number,
            'record_customer_name': self.customer_id.name,
            'record_certificate_type': self.certificates_types_id.certificate_type,
            'record_start_date': self.start_date,
            'record_expire_date': self.expire_date,
            'record_issued_by': self.issued_company_id.name,
            'record_project': self.project_id.name,
            'record_task': self.task_id.name,
            'record_user': self.user_id.name,
            'record_company': self.company_id.name,
            'record_internal_notes': self.internal_notes,
            'record_description': self.description,
            'record_achievements': self.achievements,
            'record_expire_remainder_day': self.expire_remainder_day,
            'record_product': self.product_id.name,
            'record_state': self.state
        }
        return self.env.ref(
            'certificate_license_expiry.action_certificate_report').report_action(
            None, data=data)


class CertificatesType(models.Model):
    """This is certificates type model, it is a sub model of the
    certificates"""
    _name = 'certificates.types'
    _description = "Certificates Type"
    _rec_name = 'certificate_type'

    certificate_type = fields.Char(string="Certificate Type", required=True,
                                   help="Type of certificate")
    _sql_constraints = [(
        'certificate_type_unique', 'unique(certificate_type)',
        'Already existing certificate type!')]


class CertificateTags(models.Model):
    """This is certificates tags model, it is a sub model of the
    certificates"""
    _name = 'certificates.tags'
    _description = "Certificate Tag"
    _rec_name = 'certificates_tags'

    def _get_default_color(self):
        """This will give the colors to the corresponding field"""
        return randint(1, 11)

    certificates_tags = fields.Char(string="Certificate Tag", required=True,
                                    help="Tags of certificate")
    _sql_constraints = [(
        'certificate_tag_unique', 'unique(certificates_tags)',
        'Already existing certificate tag!')]
    color = fields.Integer(string="Color", default=_get_default_color,
                           help="Color of tags")
