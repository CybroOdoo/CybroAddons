# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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
#############################################################################

import logging
from odoo import models, _

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        """Checking auto email option is set.if set email containing payslip
        details will be send on confirmation"""
        res = super(HrPayslip, self).action_payslip_done()
        if self.env['ir.config_parameter'].sudo().get_param(
                'send_payslip_by_email'):
            for payslip in self:
                if payslip.employee_id.private_email:
                    template = self.env.ref(
                        'hr_payslip_monthly_report.email_template_payslip')
                    template.sudo().send_mail(payslip.id, force_send=True)
                    _logger.info("Payslip details for %s send by mail",
                                 payslip.employee_id.name)
        return res

    def action_payslip_send(self):
        """opens a window to compose an email,
        with template message loaded by default"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
            ir_model_data._xmlid_lookup('hr_payslip_monthly_report.email_template_payslip')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'hr.payslip',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        }
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
