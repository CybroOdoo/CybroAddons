# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, api
from odoo import SUPERUSER_ID


class ReminderVisa(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def mail_reminder(self):
        today = datetime.now()
        employees = self.env['hr.employee'].search([])
        for i in employees:
            if i.birthday:
                daymonth = datetime.strptime(i.birthday, "%Y-%m-%d")
                if today.day == daymonth.day and today.month == daymonth.month:
                    self.send_birthday_wish(i.id)
        return

    @api.model
    def send_birthday_wish(self, emp_id):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        template_id = self.env['ir.model.data'].get_object_reference('birth_day_notification',
                                                                     'birthday_notification')[1]
        template_browse = self.env['mail.template'].browse(template_id)
        email_to = self.env['hr.employee'].browse(emp_id).work_email
        if template_browse:
            values = template_browse.generate_email(emp_id, fields=None)
            values['email_to'] = email_to
            values['email_from'] = su_id.email
            values['res_id'] = False
            if not values['email_to'] and not values['email_from']:
                pass
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.create(values)
            if msg_id:
                mail_mail_obj.send(msg_id)
            return True
