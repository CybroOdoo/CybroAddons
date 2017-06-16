# -*- coding: utf-8 -*-
from openerp import models
from datetime import datetime, timedelta


class ReminderVisa(models.Model):
    _inherit = 'hr.contract'

    def mail_reminder(self, cr, uid, context=None):
        i = self.pool.get('hr.config.settings').search(cr, uid,  [], limit=1, order='id desc')
        x = self.pool.get('hr.config.settings').browse(cr, uid, i and i[0], context)
        if x.visa_validity != False:
            tommorrow = datetime.now()+timedelta(days=x.limit_amount)
            date_tommorrow = tommorrow.date()
            issue_obj = self.pool.get('hr.contract')
            match = issue_obj.search(cr, uid, [('visa_expire', '<=', date_tommorrow)])
            for i in match:
                browse_hr_contract = issue_obj.browse(cr, uid, i)
                browse_id = browse_hr_contract.employee_id
                self.send_email_employee(cr, uid, browse_id.id, browse_id.name, browse_hr_contract.visa_expire,
                                         date_tommorrow, context)
        else:
            pass

    def send_email_employee(self, cr, uid, emp_id, emp_name, exp_date, no_days, context=None):
        email_template_obj = self.pool.get('email.template')
        template_ids = email_template_obj.search(cr, uid, [('name', '=', 'Visa Alert Email For Employees')], context=context)
        template_brwse = email_template_obj.browse(cr, uid, template_ids)
        email_to = self.pool.get('hr.employee').browse(cr, uid, emp_id, context).work_email
        body_html = "  Hello  "+emp_name+",<br>Your visa is going to expire on "+str(exp_date) +\
                    ". Please renew it before expiry date"
        if template_ids:
            values = email_template_obj.generate_email(cr, uid, template_ids[0], emp_id, context=context)
            values['subject'] = template_brwse.subject
            values['email_to'] = email_to
            values['body_html'] = body_html
            values['body'] = body_html
            values['email_from'] = template_brwse.email_from
            values['res_id'] = False
            mail_mail_obj = self.pool.get('mail.mail')
            msg_id = mail_mail_obj.create(cr, uid, values, context=context)
        if msg_id:
            mail_mail_obj.send(cr, uid, [msg_id], context=context)
        return True
