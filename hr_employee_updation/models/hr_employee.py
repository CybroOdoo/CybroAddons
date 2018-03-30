# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta
from odoo import models, fields, _

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeContractName(models.Model):
    _name = 'hr.emergency.contact'
    _description = 'HR Emergency Contact'

    number = fields.Char(string='Number')
    relation = fields.Char(string='Contact')
    employee_obj = fields.Many2one('hr.employee', invisible=1)


class HrEmployeeDocumentName(models.Model):
    _name = 'hr.document.document'
    _description = 'HR Employee Documents'

    name = fields.Char(string='Name')


class HrEmployeeFamily(models.Model):
    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    member_name = fields.Char(string='Name', related='employee_ref.name', store=True)
    employee_id = fields.Many2one(string="Employee", comodel_name='hr.employee', invisible=1)
    employee_ref = fields.Many2one(string="Is Employee", comodel_name='hr.employee')
    member_id = fields.Char(string='Identification No', related='employee_ref.identification_id', store=True)
    member_passport = fields.Char(string='Passport No', related='employee_ref.passport_id', store=True)
    member_passport_expiry_date = fields.Date(string='Expiry Date', related='employee_ref.passport_expiry_date',
                                              store=True)
    relation = fields.Selection([('father', 'Father'),
                                 ('mother', 'Mother'),
                                 ('daughter', 'Daughter'),
                                 ('son', 'Son'),
                                 ('wife', 'Wife')], string='Relationship')
    member_contact = fields.Char(string='Contact No', related='employee_ref.personal_mobile', store=True)
    date_of_birth = fields.Date(string="Date of Birth", related='employee_ref.birthday', store=True)
    gender = fields.Selection(string='Gender', selection=GENDER_SELECTION, related='employee_ref.gender', store=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()
    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True)
    emergency_contact = fields.One2many('hr.emergency.contact', 'employee_obj', string='Emergency Contact')
    joining_date = fields.Date(string='Joining Date')
    id_expiry_date = fields.Date(string='Expiry Date')
    passport_expiry_date = fields.Date(string='Expiry Date')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family')


class HrEmployeeAttachment(models.Model):
    _inherit = 'ir.attachment'

    id_attachment_rel = fields.Many2many('hr.employee', 'id_attachment_id', 'attach_ref', 'id_ref', string="Attachment",
                                         invisible=1)
    passport_attachment_rel = fields.Many2many('hr.employee', 'passport_attachment_id', 'attach_ref1', 'passport_ref',
                                               string="Attachment", invisible=1)
    training_attach_rel = fields.Many2many('ir.attachment', 'certificate_id', 'training_attach_id3', 'training_id',
                                           string="Certificates", invisible=1,
                                           help='You can attach the copy of your certificate')


