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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class ResCurrency(models.Model):
    """Price formats of the Propelle listings."""
    _inherit = 'res.currency'

    def _propelle_format(self, amount, compact=False):
        """Format an amount as the listings show it: no decimals, and a
        short form such as $4.8M or $890K when ``compact`` is set.

        :param float amount: amount to format.
        :param bool compact: use the short form.
        :return: the formatted amount with the currency symbol.
        """
        self.ensure_one()
        amount = amount or 0.0
        if compact and amount >= 1000000:
            number = '{:.1f}'.format(amount / 1000000).rstrip('0').rstrip('.')
            number = '{}M'.format(number)
        elif compact and amount >= 1000:
            number = '{:.0f}K'.format(amount / 1000)
        else:
            number = '{:,.0f}'.format(amount)
        symbol = self.symbol or ''
        if self.position == 'after':
            return '{} {}'.format(number, symbol).strip()
        return '{}{}'.format(symbol, number)
