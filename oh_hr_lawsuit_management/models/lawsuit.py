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
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.http import request


class HrLawsuit(models.Model):
    _name = 'hr.lawsuit'
    _description = 'Hr Lawsuit Management'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.lawsuit')
        return super(HrLawsuit, self).create(vals)

    @api.multi
    def won(self):
        self.state = 'won'

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    @api.multi
    def loss(self):
        self.state = 'fail'

    @api.multi
    def process(self):
        self.state = 'running'

    @api.depends('customer_id')
    def set_pending_invoices(self):
        for each1 in self:
            invoice_list = []
            for each in self.env['account.invoice'].sudo().search([('type', '=', 'out_invoice'), ('state', '=', 'open'),
                                                                   ('partner_id', '=', each1.customer_id.id)]):
                values = {'invoice_ref': each.id,
                          'invoice_date': each.date_invoice,
                          'due_date': each.date_due,
                          'total': each.amount_total,
                          'due_amount': each.residual}
                invoice_list.append(values)
            each1.pending_invoices = invoice_list

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=2)
        date_now = now.date()
        match = self.search([('state', '=', 'running')])
        lawsuit_managers = self.env.ref('oh_hr_lawsuit_management.lawsuit_group_manager').users
        recipient_ids = []
        for each in lawsuit_managers:
            recipient_ids.append(each.partner_id.id)
        for i in match:
            for j in i.case_record:
                if j.next_action:
                    next_action_exp_date = fields.Date.from_string(j.case_date)
                    if next_action_exp_date == date_now:
                        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                        url = base_url + _('/web#id=%s&view_type=form&model=hr.lawsuit&menu_id=') % i.id
                        mail_content = _('Hi,<br> The next action date of %s is %s. Please note it.'
                                         '<br> <div style = "text-align: left; margin-top: 16px;"><a href = "%s"'
                                         'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                                         'border-color:#875A7B;text-decoration: none; display: inline-block; '
                                         'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                                         'cursor: pointer; white-space: nowrap; background-image: none; '
                                         'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                                         'View %s</a></div>') % \
                                       (i.name, i.next_date, url, i.name)
                        main_content = {
                            'subject': _('REMINDER On Next Action of %s') % i.name,
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'recipient_ids': [(6, 0, recipient_ids)],
                        }
                        mail_id = self.env['mail.mail'].sudo().create(main_content)
                        mail_id.mail_message_id.body = mail_content
                        mail_id.send()
                        mail_id.mail_message_id.write(
                            {'needaction_partner_ids': [(4, j) for j in recipient_ids]})
                        mail_id.mail_message_id.write({'partner_ids': [(4, j) for j in recipient_ids]})

            if i.next_date:
                exp_date = fields.Date.from_string(i.next_date)
                if exp_date == date_now:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    url = base_url + _('/web#id=%s&view_type=form&model=hr.lawsuit&menu_id=') % i.id
                    mail_content = _('Hi,<br> The next hearing or next action date of %s is %s. Please note it.'
                                     '<br> <div style = "text-align: left; margin-top: 16px;"><a href = "%s"'
                                     'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                                     'border-color:#875A7B;text-decoration: none; display: inline-block; '
                                     'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                                     'cursor: pointer; white-space: nowrap; background-image: none; '
                                     'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                                     'View %s</a></div>') % \
                                   (i.name, i.next_date, url, i.name)
                    main_content = {
                        'subject': _('REMINDER On %s') % i.name,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'recipient_ids': [(6, 0, recipient_ids)],
                    }
                    mail_id = self.env['mail.mail'].sudo().create(main_content)
                    mail_id.mail_message_id.body = mail_content
                    mail_id.send()
                    mail_id.mail_message_id.write(
                        {'needaction_partner_ids': [(4, j) for j in recipient_ids]})
                    mail_id.mail_message_id.write({'partner_ids': [(4, j) for j in recipient_ids]})

    @api.depends('party2', 'employee_id', 'customer_id', 'supplier_id')
    def set_party2(self):
        for each in self:
            if each.party2 == 'employee':
                each.party2_name = each.employee_id.name
            elif each.party2 == 'supplier':
                each.party2_name = each.supplier_id.name
            elif each.party2 == 'customer':
                each.party2_name = each.customer_id.name

    name = fields.Char(string='Code', copy=False)
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    requested_date = fields.Date(string='Date', copy=False, readonly=1, default=datetime.now(),
                                 states={'draft': [('readonly', False)]})
    next_date = fields.Datetime(string='Next Hearing Date', eadonly=1, copy=False, readonly=1,
                                track_visibility='always',
                                states={'draft': [('readonly', False)]}, default=datetime.now())
    attachment_id = fields.Many2many('ir.attachment', 'case_attach_rel11', 'law_id11', 'case_id11',
                                     string="Next Hearing Requirement",
                                     help='You can attach the copy of your document')
    court_name = fields.Many2one('court.court', string='Court Name', track_visibility='always',
                                 states={'won': [('readonly', True)]})
    judge = fields.Char(string='Judge', track_visibility='always', states={'won': [('readonly', True)]})
    lawyer = fields.Char(string='Lawyer', track_visibility='always', states={'won': [('readonly', True)]})
    party1 = fields.Many2one('res.company', string='Party 1', required=1, readonly=1,
                             states={'draft': [('readonly', False)]})
    party2 = fields.Selection([('employee', 'Employee'),
                               ('supplier', 'Supplier'),
                               ('customer', 'Customer'),
                               ], string='Party 2', required=1, readonly=1, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False,
                                  readonly=1, states={'draft': [('readonly', False)]})
    customer_id = fields.Many2one('res.partner', string='Customer', copy=False,
                                  readonly=1, states={'draft': [('readonly', False)]})
    supplier_id = fields.Many2one('res.partner', string='Supplier', copy=False,
                                  readonly=1, states={'draft': [('readonly', False)]})
    party2_name = fields.Char(compute='set_party2', string='Name', store=True)
    case_record = fields.One2many('case.details', 'lawsuit_obj')
    pending_invoices = fields.One2many('law.pending.invoice', 'law_obj', compute='set_pending_invoices', readonly=1,
                                       store=True, cascade=True)
    case_details = fields.Html(string='Case Details', copy=False, track_visibility='always')
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('cancel', 'Cancelled'),
                              ('fail', 'Failed'),
                              ('won', 'Won')], string='Status',
                             default='draft', track_visibility='always', copy=False)


class CourtCourt(models.Model):
    _name = 'court.court'

    name = fields.Char(string='Name')
    place = fields.Char(string='Place')


class HrCaseDetails(models.Model):
    _name = 'case.details'
    _description = 'Case Details'

    case_date = fields.Datetime(string='Date')
    cse_details = fields.Text(string='Case Details')
    court_name = fields.Char(string='Court Name')
    next_action = fields.Char(string='Next Action')
    judge = fields.Char(string='Judge')
    lawyer = fields.Char(string='Lawyer')
    lawsuit_obj = fields.Many2one('hr.lawsuit', invisible=1)
    attachment_id = fields.Many2many('ir.attachment', 'case_attach_rel1', 'law_id1', 'case_id1',
                                     string="Attachments",
                                     help='You can attach the copy of your document')


class WizardLawsuit(models.TransientModel):
    _name = 'wizard.lawsuit'

    @api.onchange('is_next_action')
    def onchange_action(self):
        if self.is_next_action:
            self.next_date = ''
        else:
            self.next_action = ''

    @api.multi
    def follow_up(self):
        context = self._context
        lawsuit_obj = self.env['hr.lawsuit'].search([('id', '=', context.get('lawsuit_id'))])
        if self.is_next_action:
            self.env['case.details'].sudo().create({'case_date': self.next_action_date,
                                                    'cse_details': self.case_details,
                                                    'next_action': self.next_action,
                                                    'court_name': lawsuit_obj.court_name.name,
                                                    'judge': lawsuit_obj.judge,
                                                    'lawyer': lawsuit_obj.lawyer,
                                                    'lawsuit_obj': lawsuit_obj.id,
                                                    'attachment_id': [(6, 0, self.attachment_id.ids)]})
            lawsuit_obj.write({'attachment_id': [(6, 0, self.attachment_id.ids)]})
        else:
            self.env['case.details'].sudo().create({'case_date': lawsuit_obj.next_date,
                                                    'cse_details': self.case_details,
                                                    'court_name': lawsuit_obj.court_name.name,
                                                    'judge': lawsuit_obj.judge,
                                                    'lawyer': lawsuit_obj.lawyer,
                                                    'lawsuit_obj': lawsuit_obj.id,
                                                    'attachment_id': [(6, 0, self.attachment_id.ids)]})
            lawsuit_obj.write({'next_date': self.next_date,
                               'attachment_id': [(6, 0, self.attachment_id.ids)]})

    next_date = fields.Datetime(string='Next Hearing Date')
    next_action_date = fields.Datetime(string='Next Action Date')
    is_next_action = fields.Boolean(string='Is Next Action?')
    next_action = fields.Char(string='Next Action')
    case_details = fields.Text(string='Previous Case Details')
    attachment_id = fields.Many2many('ir.attachment', 'case_attach_rel', 'law_id', 'case_id',
                                     string="Next Hearing Requirement",
                                     help='You can attach the copy of your document')


class PendingInvoices(models.Model):
    _name = 'law.pending.invoice'

    law_obj = fields.Many2one('hr.lawsuit', invisible=1)
    invoice_ref = fields.Many2one('account.invoice', string='Invoice')
    invoice_date = fields.Date(string='Invoice Date')
    due_date = fields.Date(string='Due Date')
    total = fields.Float(string='Total Amount')
    due_amount = fields.Float(string='Balance Payment')


class HrEmployeeAttachmentLegal(models.Model):
    _inherit = 'ir.attachment'

    case_attach_rel = fields.Many2many('wizard.lawsuit', 'attachment_id', 'case_id', 'law_id', invisible=1)
    case_attach_rel1 = fields.Many2many('case.details', 'attachment_id', 'case_id1', 'law_id1', invisible=1)
    case_attach_rel11 = fields.Many2many('hr.lawsuit', 'attachment_id', 'case_id11', 'law_id11', invisible=1)
