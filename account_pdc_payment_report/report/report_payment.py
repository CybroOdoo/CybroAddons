# -*- coding: utf-8 -*-

import time
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ReportPayment(models.AbstractModel):
    _name = 'report.account_pdc_payment_report.report_payment_template'

    def lines(self, payment_type, journal_ids, pdc_only, data):
        domain = []
        if isinstance(journal_ids, int):
            journal_ids = [journal_ids]
            domain.append(('journal_id', 'in', journal_ids))
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
    def render_html(self, docids, data=None):
        payment_type = data['form']['payment_type']
        pdc_only = data['form']['pdc_only']
        res = {}
        for journal in data['form']['journal_ids']:
            res[journal] = self.with_context(data['form'].get('used_context', {})).lines(payment_type, journal, pdc_only, data)
        docargs = {
            'doc_ids': data['form']['journal_ids'],
            'doc_model': self.env['account.journal'],
            'data': data,
            'docs': self.env['account.journal'].browse(data['form']['journal_ids']),
            'time': time,
            'lines': res,
        }
        return self.env['report'].render('account_pdc_payment_report.report_payment_template', docargs)
