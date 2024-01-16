# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, api, _


class PaymentAcquirer(models.Model):
    """New fields are added in payment_acquirer model and compute payment
    information."""
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('myfatoorah', "MyFatoorah")],
        ondelete={'myfatoorah': 'set default'}
    )
    myfatoorah_token = fields.Char(string='Token')

    @api.model
    def _get_payment_method_information(self):
        """Fetch the payment method details"""
        res = super()._get_payment_method_information()
        res['mfatoorah'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    def _myfatoorah_get_api_url(self):
        """ Return the API URL according to the provider state.
        Note: self.ensure_one()
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://api.myfatoorah.com/'
        else:
            return 'https://apitest.myfatoorah.com/'

    @api.model
    def _create_missing_journal_for_acquirers(self, company=None):
        """Create the missing journals for payment acquirers."""
        company = company or self.env.company
        acquirers = self.env['payment.acquirer'].search(
            [('provider', '=', 'myfatoorah'), ('journal_id', '=', False),
             ('company_id', '=', company.id)])

        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank'), ('company_id', '=', company.id)], limit=1)
        if bank_journal:
            acquirers.write({'journal_id': bank_journal.id})
        return super(PaymentAcquirer,
                     self)._create_missing_journal_for_acquirers(
            company=company)

    def myfatoorah_get_form_action_url(self):
        """Get the url for the form"""
        return '/payment/myfatoorah/response'
