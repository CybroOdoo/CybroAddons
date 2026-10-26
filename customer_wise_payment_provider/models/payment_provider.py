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
from odoo import api, fields, models


class PaymentProvider(models.Model):
    """Inherited to add is_public field and to override
    _find_available_providers method"""
    _inherit = 'payment.provider'

    is_public = fields.Boolean(string='Is Public',
                               help='If true, it will be visible on the '
                                    'Website payment page.')

    @api.model
    def _find_available_providers(
            self, company_id, partner_id, amount, *, currency_id=None,
            force_tokenization=False, is_express_checkout=False,
            is_validation=False, report=None, **kwargs):
        """ Override to add the filtration based on the is_public field
        of payment provider and provider_ids field of partner"""
        # Call super to get the available providers using Odoo's standard logic
        providers = super()._find_available_providers(
            company_id, partner_id, amount, currency_id=currency_id,
            force_tokenization=force_tokenization,
            is_express_checkout=is_express_checkout,
            is_validation=is_validation, report=report, **kwargs
        )
        partner = self.env['res.partner'].browse(partner_id)
        # Filter based on is_public and provider_ids
        filtered_providers = providers.filtered(
            lambda p: p.is_public or (partner.provider_ids and p.id in partner.provider_ids.ids)
        )
        return filtered_providers
