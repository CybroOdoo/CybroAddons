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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
_logger = logging.getLogger(__name__)


class WebsiteSalePayment(WebsiteSale):
    """ For creating new record for table reservation """
    @http.route('/shop/payment/validate', type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        """ Payment Validate page """
        if sale_order_id is None:
            order = request.cart
            if not order and 'sale_last_order_id' in request.session:
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(
                    last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)

        if order and order.tables_ids and not order.table_reservation_id:
            reservation = None
            try:
                is_public = not request.env.user or request.env.user._is_public()
                customer_id = order.partner_id.id if is_public else request.env.user.partner_id.id
                reservation = request.env['table.reservation'].sudo().create({
                    "customer_id": customer_id,
                    "booked_tables_ids": order.tables_ids,
                    "floor_id": order.floors,
                    "date": order.date,
                    "starting_at": order.starting_at,
                    "ending_at": order.ending_at,
                    'booking_amount': order.booking_amount,
                    'state': 'reserved',
                    'type': 'website'
                })
            except Exception as e:
                _logger.error("Error creating table reservation: %s", e)
                
            if reservation:
                try:
                    price = order.order_line[0].price_unit if order.order_line else 0
                    string = f'The reservation amount for the selected table is {price}.' if price > 0 else ''
                    list_of_tables = [str(t) for t in reservation.booked_tables_ids.mapped('table_number')]
                    if len(list_of_tables) > 1:
                        tables_sentence = ', '.join(list_of_tables[:-1]) + ', and ' + \
                                          list_of_tables[-1]
                    else:
                        tables_sentence = list_of_tables[0] if list_of_tables else ''
                    final_sentence = string + " You have reserved table " + tables_sentence + "."
                    
                    try:
                        company = request.env.company
                        company_name = company.name or ""
                        company_phone = company.phone or ""
                        company_email = company.email or ""
                        company_website = company.website or ""
                        logo_company_id = order.company_id.id if order else company.id
                        company_logo_url = f"/logo.png?company={logo_company_id}"

                        email_link = ""
                        if company_email:
                            email_link = f'<a href="mailto:{company_email}" style="text-decoration:none; color: #5e6061;">{company_email}</a>'

                        website_link = ""
                        if company_website:
                            website_link = f'<a href="{company_website}" style="text-decoration:none; color: #5e6061;">{company_website}</a>'

                        floor_name = ""
                        if order.floors:
                            try:
                                floor_rec = request.env['restaurant.floor'].sudo().browse(int(order.floors))
                                if floor_rec.exists():
                                    floor_name = floor_rec.name or ""
                            except (ValueError, TypeError) as e:
                                _logger.debug("Failed to resolve floor name for reservation: %s", e)

                        email_body = f"""<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
    <tr>
        <td align="center">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
                <tbody>
                    <!-- HEADER -->
                    <tr>
                        <td align="center" style="min-width: 590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                <tr>
                                    <td valign="middle">
                                        <span style="font-size: 10px;">{reservation.sequence or ''}</span><br/>
                                        <span style="font-size: 20px; font-weight: bold;">Table Reservation</span>
                                    </td>
                                    <td valign="middle" align="right">
                                        <img src="{company_logo_url}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt="Logo"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="text-align:center;">
                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- CONTENT -->
                    <tr>
                        <td align="center" style="min-width: 590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                <tr>
                                    <td valign="top" style="font-size: 13px;">
                                        <div>
                                            Dear {(order.partner_id.name if is_public else request.env.user.name) or ''},<br/><br/>
                                            Your table booking at {floor_name} has been confirmed on {reservation.date} for {reservation.starting_at} to {reservation.ending_at}. {final_sentence}
                                            <br/><br/>
                                            Best regards
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align:center;">
                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- FOOTER -->
                    <tr>
                        <td align="center" style="min-width: 590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                <tr>
                                    <td valign="middle" align="left">
                                        {company_name}<br/>
                                        {company_phone}
                                    </td>
                                    <td valign="middle" align="right">
                                        {email_link}
                                        {"<br/>" if email_link and website_link else ""}
                                        {website_link}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </tbody>
            </table>
        </td>
    </tr>
</table>"""

                        email_to = order.partner_id.email if is_public else (request.env.user.login or order.partner_id.email)
                        recipient_id = order.partner_id.id if is_public else request.env.user.partner_id.id
                        if email_to:
                            request.env['mail.mail'].sudo().create({
                                'subject': "Table reservation",
                                'email_to': email_to,
                                'recipient_ids': [recipient_id] if recipient_id else [],
                                'body_html': email_body
                            }).send()
                    except Exception as e:
                        _logger.error("Error sending reservation email: %s", e)
                        
                    try:
                        order.sudo().write({'table_reservation_id': reservation.id})
                    except Exception as e:
                        _logger.error("Error writing table_reservation_id: %s", e)
                        
                except Exception as e:
                    _logger.error("Error in reservation post-processing: %s", e)
            
        return super().shop_payment_validate(sale_order_id=sale_order_id, **post)
