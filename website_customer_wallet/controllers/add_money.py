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


class WalletAmount(Controller):
    """Added amount in wallet and send mail to the user."""

    @route(['/web/add/money/<int:wallet_amount>'], csrf=False, type='json',
           auth="public",
           website=True)
    def wallet_add_amount(self, wallet_amount):
        """Add amount in wallet."""
        order = request.website.sale_get_order(force_create=True)
        loyalty_program = request.env['loyalty.program'].search(
            [('ecommerce_ok', '=', True), ('program_type', '=', 'ewallet')],
            limit=1)
        loyalty_product = loyalty_program.trigger_product_ids
        loyalty_product.write({'list_price': wallet_amount})
        sale_order_line_data = {
            'name': loyalty_product.name,
            'product_id': loyalty_product.id,
            'product_uom_qty': 1,
            'price_unit': wallet_amount,
        }
        if order:
            sale_order_line_data['order_id'] = order.id
            request.env['sale.order.line'].create(sale_order_line_data)
        else:
            sale_order = request.website.sale_get_order(force_create=True)
            sale_order_line_data['order_id'] = sale_order.id
            request.env['sale.order.line'].create(sale_order_line_data)
        request.env['customer.wallet.transaction'].create({
            'date': order.date_order,
            'partner_id': order.partner_id.id,
            'amount_type': 'added',
            'amount': wallet_amount
        })
        recipient_wallet = request.env['loyalty.card'].search(
            [('partner_id', '=', order.partner_id.id)])
        new_points = recipient_wallet.points + wallet_amount
        recipient_wallet.update({'points': new_points})
        body = f'<p>Mr {order.partner_id.name},<br>' \
               f'Amount is added. Current balance is {new_points}.</p>'
        mail_template = request.env.ref(
            'website_customer_wallet.transfer_email_template')
        mail_template.sudo().write({
            'email_to': order.partner_id.email,
            'body_html': body
        })
        mail_template.send_mail(recipient_wallet.id, force_send=True)
        return
