# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj(odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models
from odoo.osv import expression


class PaymentProvider(models.Model):
    """Inherited to add is_public field and to override
    _get_compatible_acquirers method"""
    _inherit = 'payment.acquirer'

    is_public = fields.Boolean(string='Is Public',
                               help='If true, it will be visible on the '
                                    'Website payment page.')

    @api.model
    def _get_compatible_acquirers(
            self, company_id, partner_id, currency_id=None,
            force_tokenization=False,
            is_validation=False, **kwargs
    ):
        """ Override to add the filtration based on the is_public field
        of payment acquirer and provider_ids field of partner"""
        # Compute the base domain for compatible providers.
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.provider_ids:
            domain = [('state', 'in', ['enabled', 'test']),
                      ('company_id', '=', company_id), ('is_public', '=', True)]
        else:
            domain = [('company_id', '=', company_id),
                      ('state', 'in', ['enabled', 'test']),
                      '|', ('is_public', '=', True),
                      ('id', 'in', partner.provider_ids.ids)]
        if partner.country_id:  # The partner country must either not be set or be supported
            domain = expression.AND([
                domain,
                ['|', ('country_ids', '=', False),
                 ('country_ids', 'in', [partner.country_id.id])]
            ])

        # Handle tokenization support requirements
        if force_tokenization or self._is_tokenization_required(**kwargs):
            domain = expression.AND(
                [domain, [('allow_tokenization', '=', True)]])

        compatible_acquirers = self.env['payment.acquirer'].search(domain)
        return compatible_acquirers
