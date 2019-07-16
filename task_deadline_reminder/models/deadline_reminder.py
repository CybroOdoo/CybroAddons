# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _


class DeadLineReminder(models.Model):
    _inherit = "project.task"

    task_reminder = fields.Boolean("Reminder")

    @api.model
    def _cron_deadline_reminder(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        for task in self.env['project.task'].search([]):
            if task.date_deadline !=False:
                if task.task_reminder !=False:
                    reminder_date =datetime.strptime(task.date_deadline,'%Y-%m-%d').date()
                    today =datetime.now().date()
                    if reminder_date == today:
                        if reminder_date.month == today.month:
                            if reminder_date.day == today.day:
                                if task:
                                    template_id = self.env['ir.model.data'].get_object_reference(
                                                                          'task_deadline_reminder',
                                                                          'email_template_edi_deadline_reminder')[1]
                                    email_template_obj = self.env['mail.template'].browse(template_id)
                                    if template_id:
                                        values = email_template_obj.generate_email(task.id, fields=None)
                                        values['email_from'] = su_id.email
                                        values['email_to'] = task.user_id.email
                                        values['res_id'] = False
                                        mail_mail_obj = self.env['mail.mail']
                                        msg_id = mail_mail_obj.create(values)
                                        if msg_id:
                                            msg_id.send()

        return True


