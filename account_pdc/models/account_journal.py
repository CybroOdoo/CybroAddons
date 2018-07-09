# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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

from odoo import models, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.one
    @api.depends('outbound_payment_method_ids')
    def _compute_check_printing_payment_method_selected(self):
        self.check_printing_payment_method_selected = any(
            pm.code in ['check_printing', 'pdc'] for pm in self.outbound_payment_method_ids)

    @api.model
    def _enable_pdc_on_bank_journals(self):
        """ Enables check printing payment method and add a check sequence on bank journals.
            Called upon module installation via data file.
        """
        pdcin = self.env.ref('account_pdc.account_payment_method_pdc_in')
        pdcout = self.env.ref('account_pdc.account_payment_method_pdc_out')
        bank_journals = self.search([('type', '=', 'bank')])
        for bank_journal in bank_journals:
            # bank_journal._create_check_sequence()
            bank_journal.write({
                'inbound_payment_method_ids': [(4, pdcin.id, None)],
                'outbound_payment_method_ids': [(4, pdcout.id, None)],
            })
