# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from random import randint
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class License(models.Model):
    """This will give all about license such as fields etc"""
    _name = 'certificate.license'
    _description = "License"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    state = fields.Selection(
        selection=[('new', 'New'), ('active', 'Active'),
                   ('expired_soon', 'Expiring Soon'), ('expired', 'Expired')],
        default='new', help="State of license")
    name = fields.Char(required=True, help="Name of license")
    license_number = fields.Char(readonly=True,
                                 copy=False, default='New',
                                 help="Sequence number")
    customer_id = fields.Many2one('res.partner',
                                  required=True, help="Customer")
    license_types_id = fields.Many2one('certificate.license.type',
                                       required=True,
                                       help="Type of the license")
    start_date = fields.Date(required=True,
                             default=fields.Date.context_today,
                             help="License start date")
    expire_date = fields.Date(required=True,
                              default=fields.Date.context_today,
                              help="License expiry date")
    issued_company_id = fields.Many2one('res.company', string="Issued By",
                                        required=True, help="License issued by "
                                                            "which company")
    license_tags_ids = fields.Many2many('certificate.license.tag', string="Tags",
                                        help="Tags")
    project_id = fields.Many2one('project.project',
                                 required=True, help="Project")
    task_id = fields.Many2one('project.task',
                              domain="[('project_id', '=', project_id)]",
                              required=True, help="Task")
    product_id = fields.Many2one('product.product',
                                 required=True, help="Product")
    user_id = fields.Many2one('res.users', string="Responsible Person",
                              required=True,
                              default=lambda self: self.env.user, help="User")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Company")
    expire_remainder_day = fields.Integer(string="Expiry Reminder Day",
                                          help="License expiry reminder "
                                               "day")
    login_user_id = fields.Many2one('res.users',
                                    default=lambda self: self.env.user,
                                    readonly=True, help="Login user")
    internal_notes = fields.Text(help="Internal notes")
    description = fields.Text(help="Description")
    achievements = fields.Text(help="Achievements")
    has_expired = fields.Boolean(string="Expired License",
                                 help="Becomes True if the License "
                                      "has expired", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate license sequence."""
        for vals in vals_list:
            if vals.get('license_number', 'New') == 'New':
                vals['license_number'] = (
                        self.env['ir.sequence'].next_by_code('license') or 'New'
                )
        return super().create(vals_list)

    @api.constrains('start_date', 'expire_date')
    def _constrains_license_start_date_expire_date(self):
        """Validate license start_date and expire_date."""
        for rec in self:
            if rec.start_date and rec.expire_date:
                if rec.start_date > rec.expire_date or fields.Date.today() > rec.expire_date:
                    raise ValidationError(rec.env._('Expire Date Is Not Valid'))

    def action_active_license(self):
        """It changes the state into active"""
        self.state = 'active'

    def active_license(self):
        """Compatibility method for activating license"""
        return self.action_active_license()

    def action_view_active_licenses(self):
        """It returns the license tree view"""
        return {
            'name': 'Active',
            'view_mode': 'list',
            'res_model': 'certificate.license',
            'type': 'ir.actions.act_window',
            'domain': [('state', '=', 'active')],
            'context': "{'create': False}",
        }

    def license_expiry_action(self):
        """This function is from scheduled action, it will send mail
        notification and change the state based on condition given below"""
        license_records = self.env['certificate.license'].search([
            ('has_expired', '=', False),
            ('expire_date', '!=', False),
        ])
        today = fields.Date.today()
        for rec in license_records:
            if not rec.expire_date:
                continue
            remainder_days = rec.expire_remainder_day or 0
            if remainder_days > 0 and today >= fields.Date.subtract(
                    rec.expire_date, days=remainder_days) and rec.state not in ('expired_soon', 'expired'):
                rec.write({'state': 'expired_soon'})
            if today >= rec.expire_date and rec.state != 'expired':
                rec.write({
                    'state': "expired",
                    'has_expired': True,
                })
                if rec.customer_id.email:
                    email_values = {
                        'email_cc': False,
                        'auto_delete': True,
                        'recipient_ids': [],
                        'partner_ids': [],
                        'scheduled_date': False,
                        'email_to': rec.customer_id.email,
                    }
                    template = self.env.ref(
                        'certificate_license_expiry.email_template_license',
                        raise_if_not_found=False,
                    )
                    if template:
                        template.send_mail(rec.id, force_send=True,
                                           email_values=email_values)

    def action_create_license_pdf_report(self):
        """This is used to get pdf report and passes the values to template"""
        self.ensure_one()
        data = {
            'record_name': self.name,
            'record_license_number': self.license_number,
            'record_customer': self.customer_id.name,
            'record_license_type': self.license_types_id.license_type,
            'record_start_date': self.start_date,
            'record_expire_date': self.expire_date,
            'record_issued_by': self.issued_company_id.name,
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
            'record_state': self.state,
        }
        return self.env.ref(
            'certificate_license_expiry.action_license_report').report_action(
            None, data=data)


class LicenseType(models.Model):
    """This is license type model, it is a sub model of the license """
    _name = 'certificate.license.type'
    _description = "License Type"
    _rec_name = 'license_type'

    license_type = fields.Char(required=True,
                               help="Type of license")
    _license_type_unique = models.Constraint(
        'unique (license_type)',
        "Already existing license type!",
    )


class LicenseTags(models.Model):
    """This is license tags model, it is a sub model of the license """
    _name = 'certificate.license.tag'
    _description = "License Tag"
    _rec_name = 'license_tag'

    def _get_default_color(self):
        """This will give the colors to the corresponding field"""
        return randint(1, 11)

    license_tag = fields.Char(required=True,
                              help="Tags for license")
    _license_tag_unique = models.Constraint(
        'unique (license_tag)',
        "Already existing license tag!",
    )
    color = fields.Integer(default=lambda self: self._get_default_color(),
                           help="Color of tags")
