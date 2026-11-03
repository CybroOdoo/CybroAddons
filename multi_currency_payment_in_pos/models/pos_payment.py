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


class PosPayment(models.Model):
    """Inherit pos.payment to store foreign currency details."""
    _inherit = 'pos.payment'

    payment_currency = fields.Char(
        copy=False,
        help='Currency code or symbol used for this payment.',
    )
    currency_amount = fields.Float(
        digits=(16, 2),
        copy=False,
        help='Payment amount in the selected foreign currency.',
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extend pos.payment fields loaded into the POS session cache.

        :param int or record config_id: POS configuration record or ID.
        :return: List of fields to load for pos.payment.
        :rtype: list[str]
        """
        params = super()._load_pos_data_fields(config_id)
        if not params:
            return params
        params = list(params)
        params.extend(['payment_currency', 'currency_amount'])
        return list(dict.fromkeys(params))

