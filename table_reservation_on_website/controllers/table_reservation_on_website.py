# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import datetime, timedelta
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class TableReservation(http.Controller):
    """ For reservation of tables """
    @http.route(['/table_reservation'], type='http', auth='user', website=True)
    def table_reservation(self):
        """ For rendering table reservation template """
        pos_config = request.env['pos.config'].sudo().search([
            ('module_pos_restaurant', '=', True),
            ('set_opening_hours', '=', True)
        ], limit=1)
        if not pos_config:
            pos_config = request.env['pos.config'].sudo().search([
                ('module_pos_restaurant', '=', True)
            ], limit=1)

        if pos_config and pos_config.set_opening_hours:
            opening_val = pos_config.opening_hour
            closing_val = pos_config.closing_hour
        else:
            opening_val = 0.0
            closing_val = 24.0

        try:
            opening_hour = self.float_to_time(float(opening_val))
            closing_hour = self.float_to_time(float(closing_val))
        except (ValueError, TypeError):
            opening_hour = "00:00"
            closing_hour = "23:59"

        return http.request.render(
            "table_reservation_on_website.table_reservation", {'opening_hour': opening_hour,
            'closing_hour': closing_hour})

    def float_to_time(self, hour_float):
        """ Convert float hours (e.g., 8.5 → 08:30) to HH:MM format """
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    @http.route(['/restaurant/floors'], type='http', auth='user', website=True)
    def restaurant_floors(self, **kwargs):
        """ To get floor details """
        is_lead_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.is_lead_time')
        is_lead = str(is_lead_param).lower() in ('true', '1') if is_lead_param else False
        lead_time_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.reservation_lead_time')
        lead_hours = float(lead_time_param or 0.0)
        date_str = kwargs.get('date')
        start_time_str = kwargs.get('start_time')
        if is_lead and lead_hours > 0 and date_str and start_time_str:
            try:
                booking_start_dt = datetime.strptime(f"{date_str} {start_time_str.strip()}", "%Y-%m-%d %H:%M")
                if (booking_start_dt - datetime.now()).total_seconds() / 3600.0 < lead_hours:
                    raise ValidationError(_("Reservation must be booked at least %s hour(s) in advance.") % lead_hours)
            except ValueError:
                pass

        floors = request.env['restaurant.floor'].sudo().search([])
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        refund = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.refund')
        vals = {
            'floors': floors,
            'date': kwargs.get('date'),
            'start_time': kwargs.get('start_time'),
            'end_time': kwargs.get('end_time'),
            'payment': payment,
            'refund': refund,
        }
        return http.request.render(
            "table_reservation_on_website.restaurant_floors", vals)

    @http.route(['/restaurant/floors/tables'], type='json', auth='user',
                website=True)
    def restaurant_floors_tables(self, **kwargs):
        """ To get non-reserved table details """
        table_inbetween = []
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        date_str = kwargs.get('date')
        if date_str and int(date_str.split('-')[0]) > 9999:
            return {}

        is_lead_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.is_lead_time')
        is_lead = str(is_lead_param).lower() in ('true', '1') if is_lead_param else False
        lead_time_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.reservation_lead_time')
        lead_hours = float(lead_time_param or 0.0)
        start_str = kwargs.get('start')

        if is_lead and lead_hours > 0 and date_str and start_str:
            try:
                booking_start_dt = datetime.strptime(f"{date_str} {start_str.strip()}", "%Y-%m-%d %H:%M")
                if (booking_start_dt - datetime.now()).total_seconds() / 3600.0 < lead_hours:
                    return {}
            except ValueError:
                pass

        tables = request.env['restaurant.table'].sudo().search(
            [('floor_id', '=', int(kwargs.get('floors_id')))])
        reserved = request.env['table.reservation'].sudo().search(
            [('floor_id', '=', int(kwargs.get('floors_id'))), (
                'date', '=', datetime.strptime(date_str,
                                               "%Y-%m-%d")), (
                'state', '=', 'reserved')])
        start_time_new = datetime.strptime(start_str.strip(), "%H:%M").time()
        end_str = kwargs.get('end')
        if end_str:
            end_time_new = datetime.strptime(end_str.strip(), "%H:%M").time()
        else:
            end_time_new = start_time_new
        for rec in reserved:
            start_at = datetime.strptime(rec.starting_at, "%H:%M").time()
            end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
            if start_at < end_time_new and start_time_new < end_at:
                for table in rec.booked_tables_ids:
                    table_inbetween.append(table.id)
        data_tables = {}
        for rec in tables:
            if rec.id not in table_inbetween:
                if payment:
                    data_tables[rec.id] = {}
                    data_tables[rec.id]['id'] = rec.id
                    data_tables[rec.id]['name'] = rec.table_number
                    data_tables[rec.id]['seats'] = rec.seats
                    data_tables[rec.id]['rate'] = rec.rate
                else:
                    data_tables[rec.id] = {}
                    data_tables[rec.id]['id'] = rec.id
                    data_tables[rec.id]['name'] = rec.table_number
                    data_tables[rec.id]['seats'] = rec.seats
                    data_tables[rec.id]['rate'] = 0
        return data_tables

    @http.route(['/booking/confirm'], type="http", auth="public",
                csrf=False, website=True)
    def booking_confirm(self, **kwargs):
        """ For booking tables """
        is_lead_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.is_lead_time')
        is_lead = str(is_lead_param).lower() in ('true', '1') if is_lead_param else False
        lead_time_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.reservation_lead_time')
        lead_hours = float(lead_time_param or 0.0)
        date_str = kwargs.get('date')
        start_time_str = kwargs.get('start_time') or kwargs.get('starting_at')
        if is_lead and lead_hours > 0 and date_str and start_time_str:
            try:
                booking_start_dt = datetime.strptime(f"{date_str} {start_time_str.strip()}", "%Y-%m-%d %H:%M")
                if (booking_start_dt - datetime.now()).total_seconds() / 3600.0 < lead_hours:
                    raise ValidationError(_("Reservation must be booked at least %s hour(s) in advance.") % lead_hours)
            except ValueError:
                pass

        company = request.env.company
        if kwargs.get("tables"):
            list_tables = [rec for rec in kwargs.get("tables").split(',')]
            record_tables = request.env['restaurant.table'].sudo().search(
                [('id', 'in', list_tables)])
            amount = [rec.rate for rec in record_tables]
            payment = request.env['ir.config_parameter'].sudo().get_param(
                "table_reservation_on_website.reservation_charge")
            if payment:
                table = request.env.ref(
                    'table_reservation_on_website'
                    '.product_product_table_booking').sudo()
                table.write({
                    'list_price': sum(amount)
                })
                sale_order = request.cart
                if not sale_order:
                    sale_order = request.website._create_cart()
                elif sale_order.state != 'draft':
                    request.website.sale_reset()
                    sale_order = request.website._create_cart()
                
                write_vals = {
                    'tables_ids': record_tables,
                    'floors': kwargs.get('floors'),
                    'date': kwargs.get('date'),
                    'starting_at': kwargs.get('start_time'),
                    "ending_at": kwargs.get('end_time'),
                    'booking_amount': sum(amount),
                    'order_line': [
                        (5, 0, 0),
                        (0, 0, {
                            'name': request.env.ref(
                                'table_reservation_on_website'
                                '.product_product_table_booking').name,
                            'product_id': request.env.ref(
                                'table_reservation_on_website'
                                '.product_product_table_booking').id,
                            'product_uom_qty': 1,
                            'price_unit': sum(amount),
                        })],
                }
                sale_order.sudo().write(write_vals)
                
                sale_order.website_id = request.env['website'].sudo().search(
                    [('company_id', '=', company.id)], limit=1)
                return request.redirect("/shop/cart")
            else:
                reservation = request.env['table.reservation'].sudo().create({
                    "customer_id": request.env.user.partner_id.id,
                    "booked_tables_ids": record_tables,
                    "floor_id": kwargs.get('floors'),
                    "date": kwargs.get('date'),
                    "starting_at": kwargs.get('start_time'),
                    "ending_at": kwargs.get('end_time'),
                    'booking_amount': 0,
                    'state': 'reserved',
                    'type': 'website',
                })
                string = f'The reservation amount for the selected table is {reservation.booking_amount}.' if reservation.booking_amount > 0 else ''
                list_of_tables = [str(t) for t in record_tables.mapped('table_number')]
                if len(list_of_tables) > 1:
                    tables_sentence = ', '.join(
                        list_of_tables[:-1]) + ', and ' + list_of_tables[-1]
                elif list_of_tables:
                    tables_sentence = list_of_tables[0]
                else:
                    tables_sentence = ""
                final_sentence = string + " You have reserved " + tables_sentence + "."
                company = request.env.company
                company_name = company.name or ""
                company_phone = company.phone or ""
                company_email = company.email or ""
                company_website = company.website or ""
                company_logo_url = f"/logo.png?company={company.id}"

                email_link = ""
                if company_email:
                    email_link = f'<a href="mailto:{company_email}" style="text-decoration:none; color: #5e6061;">{company_email}</a>'

                website_link = ""
                if company_website:
                    website_link = f'<a href="{company_website}" style="text-decoration:none; color: #5e6061;">{company_website}</a>'

                floor_name = request.env['restaurant.floor'].sudo().browse(int(kwargs.get('floors'))).name or ""

                body_html = f"""<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
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
                                            Dear {request.env.user.name or ''},<br/><br/>
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

                try:
                    request.env['mail.mail'].sudo().create({
                        'subject': "Table reservation",
                        'email_to': request.env.user.login,
                        'recipient_ids': [request.env.user.partner_id.id],
                        'body_html': body_html
                    }).send()
                except Exception:
                    pass
                return request.render(
                    "table_reservation_on_website.table_reserved_template")
        else:
            raise ValidationError(_("Please select table."))

    @http.route(['/table/reservation/pos'], type='json', auth='user',
                website=True)
    def table_reservation_pos(self, table_id):
        """ For pos table booking """
        table = request.env['restaurant.table'].sudo().browse(table_id)
        date_and_time = datetime.now()
        starting_at = (
            (date_and_time + timedelta(hours=5, minutes=30)).time()).strftime(
            "%H:%M")
        end_time = (
            (date_and_time + timedelta(hours=6, minutes=30)).time()).strftime(
            "%H:%M")
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        if payment:
            request.env['table.reservation'].sudo().create({
                'floor_id': table.floor_id.id,
                'booked_tables_ids': table,
                'date': date_and_time.date(),
                'starting_at': starting_at,
                'ending_at': end_time,
                'booking_amount': table.rate,
                'state': 'reserved',
                'type': 'pos'
            })
        else:
            request.env['table.reservation'].sudo().create({
                'floor_id': table.floor_id.id,
                'booked_tables_ids': table,
                'date': date_and_time.date(),
                'starting_at': starting_at,
                'ending_at': end_time,
                'booking_amount': 0,
                'state': 'reserved',
                'type': 'pos'
            })
        return

    @http.route(['/active/floor/tables'], type='json', auth='user',
                website=True)
    def active_floor_tables(self, floor_id):
        """ To get active floors """
        table_inbetween = []
        product_id = request.env.ref(
            'table_reservation_on_website.'
            'product_product_table_booking_pos')
        for rec in request.env['pos.category'].sudo().search([]):
            if rec:
                product_id.pos_categ_ids = [(4, rec.id, 0)]

        table_reservation = request.env['table.reservation'].sudo().search([(
            'floor_id', "=", floor_id), ('date', '=', datetime.now().date()),
            ('state', '=', 'reserved')])
        for rec in table_reservation:
            start_time = datetime.strptime(rec.starting_at, "%H:%M")
            start_at = start_time - timedelta(
                hours=int(rec.lead_time),
                minutes=int((rec.lead_time % 1) * 100))
            end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
            now = (
                (datetime.now() + timedelta(hours=5,
                                            minutes=30)).time()).strftime(
                "%H:%M")
            if start_at.time() <= datetime.strptime(
                    now, "%H:%M").time() <= end_at:
                for table in rec.booked_tables_ids:
                    table_inbetween.append(table.id)
        return table_inbetween
