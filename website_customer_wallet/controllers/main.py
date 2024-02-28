# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo.http import Controller, request, route


class WalletInfo(Controller):
    """Controller for the customer portal."""

    @route(['/my/wallet/info'], type='http', csrf=False, auth="user",
           website=True)
    def wallet(self):
        """Return wallet page with current wallet amount."""
        wallet_amount = request.env['loyalty.card'].search(
            [('partner_id', '=', request.env.user.partner_id.id)])
        if wallet_amount:
            data = {
                'points': wallet_amount.points}
            return request.render("website_customer_wallet.wallet_data", data)
        else:
            return request.render("website_customer_wallet.website_wallet_not_found_template")

