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
from datetime import datetime
from odoo import models, fields, api, _


class HrRewardWarning(models.Model):
    _name = 'hr.reward.warning'
    _description = 'HR Reward Warning'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def reject(self):
        self.state = 'rejected'

    @api.model
    def create(self, vals):
        if vals.get('hr_type') == 'reward':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.reward')
        elif vals.get('hr_type') == 'warning':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.warning')
        elif vals.get('hr_type') == 'letter':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.letter')
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.announcement')
        return super(HrRewardWarning, self).create(vals)

    @api.multi
    def sent(self):
        self.state = 'to_approve'

    @api.multi
    def set_to_draft(self):
        self.state = 'draft'

    @api.multi
    def approve(self):
        letter = _('<table><tr colspan="2"><td>%s</td></tr><tr><td><h4><b>Approved by</b></h4><br/>%s</td>'
                   '<td></td></tr></table>') % (self.letter, self.env.user.signature)
        partner_ids = []
        if self.letter:
            self.letter = letter
        if self.hr_type == 'warning':
            subject = 'Warning: ' + self.reason
            body = ''
        elif self.hr_type == 'reward':
            subject = 'Reward: ' + self.reason
            body = _('<h3>Congrats %s<br/></h3>') % self.employee_id.name
        elif self.hr_type == 'letter':
            subject = 'Letter: ' + self.reason
            body = ''
        if self.is_announcement:
            subject = 'Announcement: ' + self.reason
            body = ''
        if self.is_announcement:
            email_to = self.env.user.email
            emp_obj = self.env['hr.employee'].search([])
            for each in emp_obj:
                if each.work_email:
                    email_to = email_to + ',' + each.work_email
                if each.user_id:
                    partner_ids.append(each.user_id.partner_id.id)
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': body + self.letter,
                'email_to': email_to,
            }
        else:
            if self.employee_id.user_id:
                partner_ids.append(self.employee_id.user_id.partner_id.id)
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': body + self.letter,
                'email_to': self.employee_id.work_email,
            }
        mail_id = self.env['mail.mail'].create(main_content)
        if self.attachment_id:
            att_ids = []
            for each in self.attachment_id:
                att_ids.append(each.id)
            mail_id.write({'attachment_ids': [(6, 0, [aid for aid in att_ids])]})
        mail_id.send()
        mail_id.mail_message_id.write({'needaction_partner_ids': [(4, pid) for pid in partner_ids]})
        mail_id.mail_message_id.write({'partner_ids': [(4, pid) for pid in partner_ids]})
        self.state = 'approved'

    @api.multi
    def set_to_done(self):
        self.state = 'done'

    name = fields.Char(string='Code No:')
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    email_send = fields.Boolean(default=False, invisible=1, track_visibility='always', copy=False)
    is_announcement = fields.Boolean(string='Is general Announcement?')
    requested_date = fields.Date(string='Requested Date', default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True,
                                  states={'draft': [('readonly', False)]})
    hr_type = fields.Selection([('warning', 'Warning'), ('reward', 'Reward'), ('letter', 'Letter')], string='Type',
                               readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Amount')
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                     string="Attachment", help='You can attach the copy of your Letter')
    reason = fields.Text(string='Title', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    letter = fields.Html(string='Letter', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'), ('approved', 'Approved'),
                              ('done', 'Done'), ('rejected', 'Refused')], string='Status',  default='draft',
                             track_visibility='always')
    month_of_action = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'),
                                        ('4', 'April'), ('5', 'May'), ('6', 'June'),
                                        ('7', 'July'), ('8', 'August'), ('9', 'September'),
                                        ('10', 'October'), ('11', 'November'), ('12', 'December')],
                                       help="Month of action for to generate payslip",
                                       string='Requested Month', readonly=True, states={'draft': [('readonly', False)]})


class HrEmployeeWarningAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_warning_rel = fields.Many2many('hr.reward.warning', 'attachment_id', 'attach_id4', 'doc_id',
                                       string="Attachment", invisible=1)


class RewardHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    warning_amount = fields.Float('Warning Amount', compute='add_warning', store='True')
    reward_amount = fields.Float('Reward Amount', compute='add_reward', store='True')

    @api.multi
    def action_payslip_done(self):
        for each in self:
            current_month = datetime.strptime(each.date_from, "%Y-%m-%d").month
            if each.warning_amount:
                warnings = self.env['hr.reward.warning'].search([('employee_id', '=', each.employee_id.id),
                                                                 ('state', '=', 'approved'),
                                                                 ('hr_type', '=', 'warning'),
                                                                 ('month_of_action', '=', current_month)])
                for each1 in warnings:
                    each1.write({'state': 'done'})
            if each.reward_amount:
                rewards = self.env['hr.reward.warning'].search([('employee_id', '=', each.employee_id.id),
                                                                ('state', '=', 'approved'),
                                                                ('hr_type', '=', 'reward'),
                                                                ('month_of_action', '=', current_month)])
                for each1 in rewards:
                    each1.write({'state': 'done'})
        return super(RewardHrPayslip, self).action_payslip_done()

    @api.depends('employee_id')
    def add_warning(self):
        for each in self:
            warning_amount = 0
            current_month = datetime.strptime(each.date_from, "%Y-%m-%d").month
            warnings = self.env['hr.reward.warning'].search([('employee_id', '=', each.employee_id.id),
                                                             ('state', '=', 'approved'),
                                                             ('hr_type', '=', 'warning'),
                                                             ('month_of_action', '=', current_month)])
            for each1 in warnings:
                warning_amount += each1.amount
            each.warning_amount = warning_amount

    @api.depends('employee_id')
    def add_reward(self):
        for each in self:
            reward_amount = 0
            current_month = datetime.strptime(each.date_from, "%Y-%m-%d").month
            rewards = self.env['hr.reward.warning'].search([('employee_id', '=', each.employee_id.id),
                                                            ('state', '=', 'approved'),
                                                            ('hr_type', '=', 'reward'),
                                                            ('month_of_action', '=', current_month)])
            for each1 in rewards:
                reward_amount += each1.amount
            each.reward_amount = reward_amount


class WizardSendMail(models.TransientModel):
    _name = 'wizard.send.mail'

    @api.multi
    def send_now(self):
        context = self._context
        reward_obj = self.env['hr.reward.warning'].search([('id', '=', context.get('reward_id'))])
        partner_ids = []
        if reward_obj.hr_type == 'warning':
            subject = 'Warning: ' + reward_obj.reason
        elif reward_obj.hr_type == 'reward':
            subject = 'Reward: ' + reward_obj.reason
        elif reward_obj.hr_type == 'letter':
            subject = 'Letter: ' + reward_obj.reason
        if reward_obj.is_announcement:
            subject = 'Announcement: ' + reward_obj.reason
        if not reward_obj.is_announcement:
            if self.department_ids:
                body = 'Hi Team, <br/>'
                email_to = self.env.user.email
                email_ids = []
                for each in self.department_ids:
                    for each1 in each.member_ids:
                        if each1.work_email:
                            if each1.work_email not in email_ids:
                                email_ids.append(each1.work_email)
                                email_to = email_to + ',' + each1.work_email
                        if each1.user_id:
                            if each1.user_id not in partner_ids:
                                partner_ids.append(each1.user_id.partner_id.id)
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': body + reward_obj.letter,
                    'email_to': email_to,
                }
                mail_id = self.env['mail.mail'].create(main_content)
                if reward_obj.attachment_id:
                    att_ids = []
                    for each in reward_obj.attachment_id:
                        att_ids.append(each.id)
                    mail_id.write({'attachment_ids': [(6, 0, [aid for aid in att_ids])]})
                mail_id.send()
                mail_id.mail_message_id.write({'needaction_partner_ids': [(4, pid) for pid in partner_ids]})
                mail_id.mail_message_id.write({'partner_ids': [(4, pid) for pid in partner_ids]})
            reward_obj.write({'email_send': True})

    department_ids = fields.Many2many('hr.department', string='Departments')
