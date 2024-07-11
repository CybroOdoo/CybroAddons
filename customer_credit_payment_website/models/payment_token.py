# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################

from odoo import fields, models


class PaymentToken(models.Model):
    """ Inherits the 'payment.token' """
    _inherit = 'payment.token'

    credit_pay_simulated_state = fields.Selection(
        string="Simulated State",
        help="The state in which transactions created from this token should "
             "be set.",
        selection=[
            ('pending', "Pending"),
            ('done', "Confirmed"),
            ('cancel', "Canceled"),
            ('error', "Error"),
        ],
    )

    def _build_display_name(self, *args, should_pad=True, **kwargs):
        """ Override of `payment` to build the display name without padding.

        Note: self.ensure_one()

        :param list args: The arguments passed by QWeb when calling this method.
        :param bool should_pad: Whether the token should be padded or not.
        :param dict kwargs: Optional data.
        :return: The demo token name.
        :rtype: str
        """
        if self.provider_code != 'credit_pay':
            return super()._build_display_name(*args, should_pad=should_pad,
                                               **kwargs)
        return super()._build_display_name(*args, should_pad=False, **kwargs)
