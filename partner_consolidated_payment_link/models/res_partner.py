# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
import uuid

from odoo import models
from odoo.tools import consteq, hmac
from odoo.addons.payment import utils as payment_utils


class ResPartner(models.Model):
    """Inherit Res Partner to add helper methods for consolidated payment links."""
    _inherit = 'res.partner'


    def _get_overdue_amls_domain(self):
        """
        This function returns a domain to find overdue account.move.line
        records (invoice lines) for the current partner.

        :return: A list of tuples representing an Odoo domain.
        """
        partner_ids = self.env['res.partner'].search([('id', 'child_of', self.id)])
        domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.payment_state', 'in', ('not_paid', 'partial')),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('reconciled', '=', False),
            ('move_id.partner_id', 'in', partner_ids.ids)
        ]
        return domain

    def get_overdue_amls(self):
        """
        The function to fetch the actual overdue account.move.line records.
        """
        domain = self._get_overdue_amls_domain()
        return self.env['account.move.line'].sudo().search(domain)

    def get_total_due(self, company):
        """
        Get the total due of the given partner for the company
        :param company: record of res.company
        :return: total_due
        :rtype: float
        """
        self.ensure_one()
        account_receivable_lines = self.get_overdue_amls()
        total_due = sum(
            line.amount_residual_currency if line.currency_id and line.company_id.currency_id else line.amount_residual
            for line in account_receivable_lines if line.company_id == company)
        return total_due

    def get_total_due_in_company_currency(self):
        """
        Compute the total outstanding due amount of the partner in the current company's currency.
        :return: total_due
        :rtype: float
        """
        total_due = 0
        for aml in self.get_overdue_amls():
            if aml.company_id == self.env.company:
                total_due += aml.amount_residual
        return total_due

    def get_access_token(self, amount_residual, currency_id):
        """Generate access token for payment validation.

        :param amount_residual: Total amount residual due
        :param currency_id: ID of currency record
        :return: Security access token string
        """
        self.ensure_one()
        return payment_utils.generate_access_token(self.id, amount_residual, currency_id)

    def _get_consolidated_payment_token(self):
        """Return the token protecting the consolidated payment link of the partner.

        :return: Security access token string
        """
        self.ensure_one()
        return hmac(self.env(su=True), 'partner_consolidated_payment_link', self.id)

    def _check_consolidated_payment_token(self, access_token):
        """Check the token received on the consolidated payment link.

        :param access_token: Token received in the link
        :return: True if the token is valid for the partner
        """
        self.ensure_one()
        return bool(access_token) and consteq(
            access_token, self._get_consolidated_payment_token())

    def _get_consolidated_payment_url(self):
        """Return the public URL of the consolidated payment link of the partner."""
        self.ensure_one()
        base_url = self.get_base_url()
        return f"{base_url}/payment/balance/{self.id}?access_token={self._get_consolidated_payment_token()}"

    def _get_consolidated_payment_reference(self, moves):
        """Return the reference shared by the given invoices, creating it if needed.

        The existing reference is reused as long as all the invoices share it, so
        that opening the link several times does not rewrite the invoices.

        :param moves: account.move records to be paid together
        :return: The consolidated payment reference
        """
        reference = moves[:1].consolidated_payment_link_ref
        if not reference or any(move.consolidated_payment_link_ref != reference for move in moves):
            reference = str(uuid.uuid4())
            moves.write({'consolidated_payment_link_ref': reference})
        return reference

    def _prepare_consolidated_payment_values(self, company=None):
        """Compute the values needed to pay all the overdue invoices of the partner.

        :param company: record of res.company, defaults to the partner's company
            or to the company of its overdue invoices
        :return: dict with the reference, amount, currency and company, or None
            if nothing is due
        """
        self.ensure_one()
        overdue_amls = self.get_overdue_amls()
        if not overdue_amls:
            return None
        company = company or self.company_id or overdue_amls[0].company_id
        currency = overdue_amls[0].currency_id
        total_due = self.get_total_due(company)
        if len(overdue_amls.currency_id) > 1:
            currency = company.currency_id
            total_due = self.with_company(company).get_total_due_in_company_currency()
        return {
            'reference': self._get_consolidated_payment_reference(overdue_amls.move_id),
            'amount': currency.round(total_due),
            'currency': currency,
            'company': company,
        }
