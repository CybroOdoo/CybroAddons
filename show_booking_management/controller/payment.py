# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import base64
import json
from io import BytesIO
import qrcode
from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing


class PaymentPost(PaymentPostProcessing):
    """
        Inherit the poll status method to handle payment status completion.
        Creates movie registration and movie seats records if payment status is 'done'.
    """
    @http.route()
    def poll_status(self, **kwargs):
        """ Inheriting the poll status and if the status of payment is done
        it will create records movie registration and movie seats."""
        res = super(PaymentPost, self).poll_status(**kwargs)
        movie_booking_data = request.session.get('movie_booking_data')
        if movie_booking_data and res['state'] == 'done':
            movie_booking_data = json.loads(movie_booking_data)
            # Creating movie.registration record
            movie_ticket = request.env['movie.registration'].create({
                'movie_id': movie_booking_data['movie_id'],
                'screen_id': movie_booking_data['screen_id'],
                'time_slot_id': movie_booking_data['time_slot_id'],
                'date': movie_booking_data['booking_date'],
                'no_of_tickets': len(movie_booking_data['selected_seats']),
                'partner_id': request.env.user.partner_id.id,
                'state': 'invoiced'
            })
            # Creating QR code
            qr_data = f"Ticket : {movie_ticket.name}\n" \
                      f"Movie: {movie_ticket.movie_id.name}\n" \
                      f"Date: {movie_ticket.date}\n" \
                      f"Time: {movie_ticket.time_slot_id.name}\n" \
                      f"Screen: {movie_ticket.screen_id.name}\n" \
                      f"Seats: {', '.join(movie_booking_data['selected_seats'])}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image()
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode()
            movie_ticket.write({'qr_code': qr_image})

            # Creating movie.seats records
            for seat in movie_booking_data['selected_seats']:
                request.env['movie.seats'].create({
                    'screen_id': movie_booking_data['screen_id'],
                    'time_slot_id': movie_booking_data['time_slot_id'],
                    'movie_registration_id': movie_ticket.id,
                    'date': movie_booking_data['booking_date'],
                    'seat': seat,
                    'is_booked': True
                })
            invoice = request.env['account.move'].browse(
                movie_booking_data['invoice_id'])
            invoice.movie_ticket_id = movie_ticket.id
            movie_admin_users = request.env['res.users'].search([
                ('groups_id', 'in',
                 request.env.ref('show_booking_management.show_booking_management_group_admin').id)
            ])
            template = request.env.ref(
                'show_booking_management.email_template_movie_ticket')
            attachment_id = request.env['ir.attachment'].create({
                'name': 'Movie_Ticket_QR_Code.png',
                'type': 'binary',
                'datas': qr_image,
                'res_model': 'movie.registration',
                'res_id': movie_ticket.id,
                'mimetype': 'image/png'
            })
            email_values = {
                'email_from': movie_admin_users[0].email,
                'attachment_ids': [(6, 0, [attachment_id.id])],
            }
            template.send_mail(movie_ticket.id, email_values=email_values, force_send=True)
        return res
