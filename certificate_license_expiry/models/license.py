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


class License(models.Model):
    """This will give all about license such as fields etc"""
    _name = 'license'
    _description = "License"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection(
        selection=[('new', 'New'), ('active', 'Active'),
                   ('expired_soon', 'Expired Soon'), ('expired', 'Expired')],
        string="State", default='new', help="Sates of certificate")
    name = fields.Char(string='Name', required=True, help="Name of certificate")
    license_number = fields.Char(string="Certificate Number", readonly=True,
                                 copy=False, default='New',
                                 help="Sequence number")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  required=True, help="Customer")
    license_types_id = fields.Many2one('license.types',
                                       string="License Types", required=True,
                                       help="Type of the "
                                            "license")
    start_date = fields.Date(string="Start Date", required=True,
                             default=fields.Date.today(), help="License"
                                                               "start date")
    expire_date = fields.Date(string="Expire Date", required=True,
                              default=fields.Date.today(),
                              help="License expiry "
                                   "date")
    issued_company_id = fields.Many2one('res.company', string="Issued By",
                                        required=True, help="License issued by "
                                                            "which company")
    license_tags_ids = fields.Many2many('license.tags', string="Tags",
                                        help="Tags")
    project_id = fields.Many2one('project.project', string="Project",
                                 required=True, help="Project")
    task_id = fields.Many2one('project.task', string="Task",
                              domain="[('project_id', '=', project_id)]",
                              required=True, help="Task")
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, help="Product")
    user_id = fields.Many2one('res.users', string="Responsible Person",
                              required=True,
                              default=lambda self: self.env.user, help="User")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Company")
    expire_remainder_day = fields.Integer(string="Expire Reminder Day",
                                          help="License expire remainder"
                                               "day")
    login_user_id = fields.Many2one('res.users', string='Login User',
                                    default=lambda self: self.env.user,
                                    readonly=True, help="Login user")
    internal_notes = fields.Text(string="Internal Notes", help="Internal notes")
    description = fields.Text(string="Description", help="Description")
    achievements = fields.Text(string="Achievements", help="Achievements")
    has_expired = fields.Boolean(string="Expired License",
                                 help="Becomes True if the License "
                                      "has expired")

    @api.model
    def create(self, vals):
        """This is used to get the license number"""
        if vals.get('license_number', 'New') == 'New':
            vals['license_number'] = self.env['ir.sequence'].next_by_code(
                'license') or 'New'
        result = super(License, self).create(vals)
        return result

    @api.constrains('start_date', 'expire_date')
    def _constrains_license_start_date_expire_date(self):
        """This will give validation at the time of expired date and start
        date have any problem"""
        if self.start_date and self.expire_date:
            if self.start_date > self.expire_date or fields.Date.today() > self.expire_date:
                raise ValidationError(_('Expire Date Is Not Valid'))

    def active_license(self):
        """It changes the state into active"""
        self.state = 'active'

    def action_active_license(self):
        """It returns the license tree view"""
        return {
            'name': 'Active',
            'view_mode': 'tree',
            'res_model': 'license',
            'type': 'ir.actions.act_window',
            'domain': [('state', '=', 'active')],
            'context': "{'create': False}"
        }

    def license_expiry_action(self):
        """This function is from scheduled action, it will send mail
        notification and change the state based on condition given below"""
        license = self.env['license'].search([('has_expired', '=', False)])
        today = fields.Date.today()
        for rec in license:
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
                    'certificate_license_expiry.email_template_license')
                template.send_mail(rec.id, force_send=True,
                                   email_values=email_values)
                rec.state = 'expired'
                rec.has_expired = True

    def action_create_license_pdf_report(self):
        """This is used to get pdf report and passes the values to template"""
        data = {
            'record_name': self.name,
            'record_license_number': self.license_number,
            'record_customer': self.customer_id.name,
            'record_license_type': self.license_types_id.license_type,
            'record_start_date': self.start_date,
            'record_expire_date': self.expire_date,
            'record_issued_by_': self.issued_company_id.name,
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
            'certificate_license_expiry.action_license_report').report_action(
            None, data=data)


class LicenseType(models.Model):
    """This is license type model, it is a sub model of the license """
    _name = 'license.types'
    _description = "License Type"
    _rec_name = 'license_type'

    license_type = fields.Char(string="License Type", required=True,
                               help="Type of license")


class LicenseTags(models.Model):
    """This is license tags model, it is a sub model of the license """
    _name = 'license.tags'
    _description = "License Tag"
    _rec_name = 'license_tags_ids'

    def _get_default_color(self):
        """This will give the colors to the corresponding field"""
        return randint(1, 11)

    license_tags_ids = fields.Char(string="License Tag", required=True,
                                   help="Tags fpr license")
    color = fields.Integer(string="Color", default=_get_default_color,
                           help="Color of tags")
