# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fasluca(<faslu@cybrosys.in>)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import logging

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportPayment(models.AbstractModel):
    _name = 'report.account_pdc_payment_report.report_payment_template'

    def get_lines(self, payment_type, journal_id, pdc_only, data):
        domain = []
        if journal_id:
            domain.append(('journal_id', '=', journal_id))
        if payment_type == 'inbound':
            domain.append(('payment_type', '=', 'inbound'))
        elif payment_type == 'outbound':
            domain.append(('payment_type', '=', 'outbound'))
        if data['form']['date_from']:
            domain.append(('payment_date', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('payment_date', '<=', data['form']['date_to']))
        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id'][0]))
        if pdc_only:
            domain.append(('payment_method_id.code', '=', 'pdc'))
            if data['form']['effective_date_from']:
                domain.append(('effective_date', '>=', data['form']['effective_date_from']))
            if data['form']['effective_date_to']:
                domain.append(('effective_date', '<=', data['form']['effective_date_to']))
        return self.env['account.payment'].search(domain)

    @api.model
    def get_report_values(self, docids, data=None):
        if not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        payment_type = data['form']['payment_type']
        pdc_only = data['form']['pdc_only']
        lines = {}
        for journal in data['form']['journal_ids']:
            lines[journal] = self.with_context(data['form'].get('used_context', {})).get_lines(payment_type, journal, pdc_only, data)
            print(lines[journal])
        model = self.env.context.get('active_model')
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data,
            'docs': self.env['account.journal'].browse(data['form']['journal_ids']),
            'lines': lines,
        }
