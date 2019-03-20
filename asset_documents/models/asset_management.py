# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

class AssetCatagory(models.Model):
    _inherit = 'account.asset.category'

    category_code = fields.Char(string='Category Code')
    next_number = fields.Integer(string='Next Number', default=1)
    padding = fields.Integer(string='Padding',
                             default=4,
                             help='If padding is 4 then the sequence number will be 3 digit number, eg 0009,0055,0471')


class AssetManagment(models.Model):
    _inherit = 'account.asset.asset'


    documents = fields.One2many('account.asset.document', 'document', string='Documents')
    sequence_number = fields.Text(string="Number")
    description = fields.Html(string='Notes')

    @api.onchange('category_id')
    def _onchange_asset_catagory(self):
        
        # interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix
        self.sequence_number = str(self.category_id.category_code) + '%%0%sd' % self.category_id.padding % self.category_id.next_number

    @api.model
    def create(self, vals):
        
        if vals['category_id']:
            obj=self.env['account.asset.category'].search([('id','=',vals['category_id'])])
            obj.next_number = obj.next_number + 1
        # self.category_id.next_number = self.category_id.next_number + 1
        return super(AssetManagment,self).create(vals)


class AssetDocument(models.Model):
    _name = 'account.asset.document'

    document = fields.Many2one('account.asset.asset')
    document_name = fields.Char(string='Document', required=True, copy=False, help="You can give your Document name or number.")
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    doc_attachment_id = fields.Many2many('ir.attachment', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)
    warning_before = fields.Integer(string='Before',help="Number of days before the expiry date to get the warning message")
    repeat = fields.Boolean(string='Repeat', help="Tick the check box for repeated notification. For example EMIs")
    period_type = fields.Selection([('day', 'Daily'),
                                    ('week', 'Weekily'),
                                    ('month', 'Monthly'),
                                    ('year', 'Yearly')],
                                   string='Period Type',
                                   help="Type of reminder you need. If you select Monthly then you will get notification on every month.")
    no_of_periods = fields.Integer(string='Period',
                                   default=1,
                                   help="Period of repetition. If you put 3 then you will get notification in every 3 day/week/month/year resepectively")

    def create(self,val):
        flag=0
        for data in val:
            if data['repeat']:
                if not(data['period_type'] and data['no_of_periods'] and data['expiry_date']):
                    flag=1
        if flag:
            raise Warning(("Some fields are missing. Please check Period Type, Period and expiry Date"))
        else:
            return super(AssetDocument, self).create(val)

    def asset_mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        
        emp_list=[]
        groups = self.env['res.groups'].search([('id','=',45)])
        
        for usr in groups.users:
            emp = self.env['hr.employee'].search([('user_id','=',usr.id)])
            if emp.id:
                emp_list.append(emp.work_email)
        for i in match:
            if i.expiry_date:
                exp_date = i.expiry_date - timedelta(days=i.warning_before)
                if date_now >= exp_date:
                    mail_content = "  CHECK ,<br>The Document " + i.document_name + " of the asset " + i.document.name + " is going to expire on " + \
                                   str(i.expiry_date) + ". Please renew it before expiry date."
                    main_content = {
                        'subject': _('Asset Document-%s Expired On %s') % (i.document_name, i.expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': ', '.join(emp_list),
                    }
                    self.env['mail.mail'].create(main_content).send()
            if i.expiry_date == date_now:
                if i.repeat:
                    if i.period_type == 'day':
                        i.expiry_date = i.expiry_date + timedelta(days=i.no_of_periods)
                    elif i.period_type == 'week':
                        i.expiry_date = i.expiry_date + timedelta(weeks=i.no_of_periods)
                    elif i.period_type == 'month':
                        i.expiry_date = i.expiry_date + relativedelta(months=+i.no_of_periods)
                    else:
                        i.expiry_date = i.expiry_date + relativedelta(years=+i.no_of_periods)