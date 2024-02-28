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
from odoo.http import Controller, route, request
from odoo import http


class WalletTransactions(Controller):
    """Controller for handling wallet transactions."""

    @route(['/web/wallet/transactions/'], type='json', csrf=False,
           auth="user", website=True)
    def transaction_history(self):
        """Rendering transactions details into wallet transactions history
        template."""
        transactions = request.env['customer.wallet.transaction'].search([])
        if transactions:
            values = {
                'transactions': transactions
            }
            response = http.Response(
                template='website_customer_wallet.wallet_history_data',
                qcontext=values)
            rendered_template = response.render()
            return rendered_template
        else:
            response = http.Response(
                template='website_customer_wallet.no_histories')
            rendered_template = response.render()
            return rendered_template
