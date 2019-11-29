# -*- coding: utf-8 -*-

import datetime
from datetime import datetime
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _


class DeadLineReminder(models.Model):
    _inherit = "project.task"

    task_reminder = fields.Boolean("Reminder")

    @api.model
    def _cron_deadline_reminder(self):
        print("test")
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        print(su_id)
        for task in self.env['project.task'].search([('date_deadline', '!=', None),
                                                     ('task_reminder', '=', True), ('user_id', '!=', None)]):
            print(task, "task")
            reminder_date = task.date_deadline
            today = datetime.now().date()
            if reminder_date == today and task:
                # print("kkkkkkkkkkkkkkk")
                template_id = self.env['ir.model.data'].get_object_reference(
                    'task_deadline_reminder',
                    'email_template_edi_deadline_reminder')[1]
                if template_id:
                #     print("template_id", template_id)
                    email_template_obj = self.env['mail.template'].browse(template_id)
                #     print("email_template_obj", email_template_obj)
                    values = email_template_obj.generate_email(task.id, fields=None)
                    msg_id = self.env['mail.mail'].create(values)
                    if msg_id:
                        msg_id._send()

        return True


