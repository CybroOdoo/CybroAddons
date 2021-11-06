# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError


class LogsScheduledActions(models.Model):
    _description = "Error log"
    _name = 'logs.action'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'ir.cron']

    name = fields.Char(string="Name", required=True, track_visibility='always')
    method = fields.Char(string="Method", track_visibility='always')
    created_by = fields.Many2one('res.users', string="Created by", default=lambda self: self.env.user, index=True)
    object_action = fields.Char(string="Object", track_visibility='always')
    exec_date = fields.Datetime(string="Execution Date Time")
    company_name = fields.Many2one('res.company', string="Company",  default=lambda self: self.env.user.company_id,
                                   index=True)
    stages_id = fields.Selection(
        [('new', 'New'), ('confirm', 'Confirmed'), ('resolved', 'Resolved'), ('cancelled', 'Cancelled')], default='new')
    error_details = fields.Char(string="Error details", track_visibility='always')

    @api.multi
    def action_mail_send(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('cron_failure_notification',
                                                         'scheduler_error_mailer')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'logs.action',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def button_confirm_action(self):
        self.stages_id = 'confirm'

    def button_resolved_action(self):
        self.stages_id = 'resolved'

    def button_cancel_action(self):
        self.stages_id = 'cancelled'

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    @api.model
    def _handle_callback_exception(
            self, model_name, method_name, args, job_id, job_exception):
        res = super(IrCron, self)._handle_callback_exception(
            model_name, method_name, args, job_id, job_exception)
        my_cron = self.browse(job_id)
        self.env['logs.action'].create({
            'name': my_cron.name,
            'method': my_cron.model,
            'object_action': my_cron.function,
            'exec_date': datetime.datetime.now(),
            'error_details': str(job_exception),
        })

        return res

    @api.model
    def _test_scheduler_failure(self):
        """This function is used to test and debug this module"""

        raise UserError(
            _("Task failure with UID = %d.") % self._uid)
