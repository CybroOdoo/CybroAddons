# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhu Krishnan (odoo@cybrosys.com)
#
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
################################################################################
from odoo import api, fields, models
from odoo.osv import expression


class PaymentProvider(models.Model):
    """Inherited to add is_public field and to override
    _get_compatible_providers method"""
    _inherit = 'payment.provider'

    is_public = fields.Boolean(string='Is Public',
                               help='If true, it will be visible on the '
                                    'Website payment page.')

    @api.model
    def _get_compatible_providers(
            self, company_id, partner_id, amount, currency_id=None,
            force_tokenization=False, is_express_checkout=False,
            is_validation=False, **kwargs):
        """ Override to add the filtration based on the is_public field
        of payment provider and provider_ids field of partner"""
        # Compute the base domain for compatible providers.
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.provider_ids:
            domain = [('state', 'in', ['enabled', 'test']),
                      ('company_id', '=', company_id), ('is_public', '=', True)
                      ]
        else:
            domain = [('company_id', '=', company_id),
                      ('state', 'in', ['enabled', 'test']),
                      '|', ('is_public', '=', True),
                      ('id', 'in', partner.provider_ids.ids)]
        # Handle the is_published state.
        if not self.env.user._is_internal():
            domain = expression.AND([domain, [('is_published', '=', True)]])
        # Handle partner country.
        if partner.country_id:  # The partner country must either not be set
            # or be supported.
            domain = expression.AND([
                domain, [
                    '|',
                    ('available_country_ids', '=', False),
                    ('available_country_ids', 'in', [partner.country_id.id]),
                ]
            ])
        # Handle the maximum amount.
        currency = self.env['res.currency'].browse(currency_id).exists()
        if not is_validation and currency:  # The currency is required to
            # convert the amount.
            company = self.env['res.company'].browse(company_id).exists()
            date = fields.Date.context_today(self)
            converted_amount = currency._convert(amount, company.currency_id,
                                                 company, date)
            domain = expression.AND([
                domain, [
                    '|', '|',
                    ('maximum_amount', '>=', converted_amount),
                    ('maximum_amount', '=', False),
                    ('maximum_amount', '=', 0.),
                ]
            ])
        # Handle tokenization support requirements.
        if force_tokenization or self._is_tokenization_required(**kwargs):
            domain = expression.AND(
                [domain, [('allow_tokenization', '=', True)]])
        # Handle express checkout.
        if is_express_checkout:
            domain = expression.AND(
                [domain, [('allow_express_checkout', '=', True)]])
        compatible_providers = self.env['payment.provider'].search(domain)
        return compatible_providers
