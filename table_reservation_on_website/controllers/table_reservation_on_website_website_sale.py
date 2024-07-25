# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import SUPERUSER_ID


class WebsiteSalePayment(WebsiteSale):
    """ For creating new record for table reservation """
    @http.route('/shop/payment/validate', type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        """ Payment Validate page """
        if sale_order_id is None:
            order = request.website.sale_get_order()
            if not order and 'sale_last_order_id' in request.session:
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(
                    last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')
        errors = self._get_shop_payment_errors(order)
        if errors:
            first_error = errors[0]  # only display first error
            error_msg = f"{first_error[0]}\n{first_error[1]}"
            raise ValidationError(error_msg)
        tx_sudo = order.get_portal_last_transaction() if order else order.env['payment.transaction']
        if order.tables_ids:
            reservation = request.env['table.reservation'].sudo().create({
                "customer_id": request.env.user.partner_id.id,
                "booked_tables_ids": order.tables_ids,
                "floor_id": order.floors,
                "date": order.date,
                "starting_at": order.starting_at,
                "ending_at": order.ending_at,
                'booking_amount': order.booking_amount,
                'state': 'reserved',
                'type': 'website'
            })
            string = f'The reservation amount for the selected table is {order.order_line[0].price_unit}.' if order.order_line[0].price_unit > 0 else ''
            list_of_tables = reservation.booked_tables_ids.mapped('name')
            if len(list_of_tables) > 1:
                tables_sentence = ', '.join(list_of_tables[:-1]) + ', and ' + \
                                  list_of_tables[-1]
            else:
                tables_sentence = list_of_tables[0]
            final_sentence = string + " You have reserved table " + tables_sentence + "."
            request.env['mail.mail'].sudo().create({
                'subject': "Table reservation",
                'email_to': request.env.user.login,
                'recipient_ids': [request.env.user.partner_id.id],
                'body_html':
                    '<table border=0 cellpadding=0 cellspacing=0 '
                    'style="padding-top: 16px; background-color: '
                    '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                    'color: #454748; width: 100%; '
                    'border-collapse:separate;"><tr><td align=center>'
                    '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                    '<tbody>'
                    '<!-- HEADER -->'
                    '<tr>'
                    '<td align=center style="min-width: 590px;">'
                    '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                    '<tr>'
                    '<td valign=middle>'
                    '<span style="font-size: 10px;">'+reservation.sequence+'</span><br/>'
                    '<span style="font-size: 20px; font-weight: bold;">' + 'Table Reservation' + '</span>'
                     '</td>'
                     '<td valign="middle" align="right">'
                     '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                     '</td>'
                     '</tr>'
                     '<tr>''<td colspan="2" style="text-align:center;">'
                     '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                     '</td>''</tr>'
                     '</table>'
                     '</td>'
                     '</tr>'
                     '<!-- CONTENT -->'
                     '<tr>'
                     '<td align="center" style="min-width: 590px;">'
                     '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                     '<tr>'
                     '<td valign="top" style="font-size: 13px;">'
                     '<div>'
                     'Dear' + ' ' + request.env.user.name + ',' '<br/>''<br/>'
                    'Your table booking at ' + request.env['restaurant.floor'].browse(int(order.floors)).name + ' ' + 'has been confirmed on '+str(reservation.date)+' for '+reservation.starting_at+' to '+reservation.ending_at + '.' + final_sentence +
                    '<br/>''<br/>'
                    '</span>'
                    '</div>'
                    '<br/>'
                    'Best regards''<br/>'
                    '</div>'
                    '</td>'
                    '</tr>'
                    '<tr>'
                    '<td style="text-align:center;">'
                    '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                    '</td>'
                    '</tr>'
                    '</table>'
                    '</td>'
                    '</tr>'
                    '<!-- FOOTER -->'
                    '<tr>'
                    '<td align="center" style="min-width: 590px;">'
                    '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                    '<tr>'
                    '<td valign="middle" align="left">'
                    + request.env.company.name +
                    '<br/>'
                    + request.env.company.phone +
                    '</td>'
                    '<td valign="middle" align="right">'
                    '<t t-if="%s" % +self.env.company_id.email>'
                    '<a href="mailto:%s % +request.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                    + request.env.company.email +
                    '</a>'
                    '</t>'
                    '<br/>'
                    '<t t-if="%s % +self.env.company.website+ ">'
                    '</table>'
            }).send()
            order.table_reservation_id = reservation.id
        if not order or (order.amount_total and not tx_sudo):
            return request.redirect('/shop')
        if order and not order.amount_total and not tx_sudo:
            order.with_context(send_email=True).with_user(SUPERUSER_ID).action_confirm()
            return request.redirect(order.get_portal_url())
        request.website.sale_reset()
        if tx_sudo and tx_sudo.state == 'draft':
            return request.redirect('/shop')
        return request.redirect('/shop/confirmation')
