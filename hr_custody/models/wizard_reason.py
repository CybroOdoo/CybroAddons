# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Authors: Avinash Nk, Jesni Banu (<https://www.cybrosys.com>)
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
from odoo import models, fields, api, _


class WizardReason(models.TransientModel):
    """
        Hr custody contract refuse wizard.
            """
    _name = 'wizard.reason'

    @api.multi
    def send_reason(self):
        context = self._context
        reject_obj = self.env[context.get('model_id')].search([('id', '=', context.get('reject_id'))])
        if 'renew' in context.keys():
            reject_obj.write({'state': 'approved',
                              'renew_reject': True,
                              'renew_rejected_reason': self.reason})
        else:
            if context.get('model_id') == 'hr.holidays':
                reject_obj.write({'rejected_reason': self.reason})
                reject_obj.action_refuse()
            else:
                reject_obj.write({'state': 'rejected',
                                  'rejected_reason': self.reason})

    reason = fields.Text(string="Reason")
