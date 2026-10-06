# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo import models

from odoo.addons.payment import utils as payment_utils

class ResPartner(models.Model):
    """
    Inherit res.partner to compute overdue account move lines and calculate
    total outstanding due amounts for generating payment links.
    """
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

    def get_consolidated_total_due(self, company):
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
        overdue_amls = self.get_overdue_amls().filtered(lambda aml: aml.company_id == self.env.company)
        return sum(overdue_amls.mapped('amount_residual'))

    def get_access_token(self, amount_residual, currency_id):
        """
        Method to generate access token.
        """
        self.ensure_one()
        return payment_utils.generate_access_token(self.id, amount_residual, currency_id)
