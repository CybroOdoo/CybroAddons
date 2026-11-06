# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models

WALLET_MODULE = 'pos_customer_wallet_management'


class AccountChartTemplate(models.AbstractModel):
    """Recreate the wallet records after a chart of accounts is loaded"""
    _inherit = 'account.chart.template'

    def _post_load_data(self, template_code, company, template_data):
        """Loading a chart of accounts on a company without accounting
        deletes its journals, including the wallet journal and its payment
        method. Recreate them once the chart is loaded."""
        res = super()._post_load_data(template_code, company, template_data)
        self._ensure_wallet_records(company)
        return res

    def _ensure_wallet_records(self, company):
        """Create the wallet journal and payment method if they are missing.

        :param company: the company the records belong to
        """
        if company != self.env.ref('base.main_company'):
            return
        ref = self.env.ref
        journal = ref(f'{WALLET_MODULE}.pos_wallet_journal_main',
                      raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'POS Wallet',
                'code': 'WLT',
                'type': 'bank',
                'is_wallet_journal': True,
                'company_id': company.id,
            })
            self.env['ir.model.data']._update_xmlids([{
                'xml_id': f'{WALLET_MODULE}.pos_wallet_journal_main',
                'record': journal,
                'noupdate': False,
            }])
        payment_method = ref(
            f'{WALLET_MODULE}.pos_wallet_payment_method_main',
            raise_if_not_found=False)
        if not payment_method:
            payment_method = self.env['pos.payment.method'].create({
                'name': 'Wallet',
                'type': 'bank',
                'journal_id': journal.id,
            })
            self.env['ir.model.data']._update_xmlids([{
                'xml_id': f'{WALLET_MODULE}.pos_wallet_payment_method_main',
                'record': payment_method,
                'noupdate': False,
            }])
