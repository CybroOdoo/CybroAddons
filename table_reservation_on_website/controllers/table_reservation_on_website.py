# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request


class TableReservation(http.Controller):
    """For table reservation"""

    @http.route(['/table_reservation'], type='http', auth='user', website=True)
    def table_reservation(self):
        """For render table reservation template"""
        return http.request.render(
            "table_reservation_on_website.table_reservation", {})

    @http.route(['/restaurant/floors'], type='http', auth='user', website=True)
    def restaurant_floors(self, **kwargs):
        """To get floor details"""
        floors = request.env['restaurant.floor'].search([])
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
        """To get non-reserved table details"""
        table_inbetween = []
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        tables = request.env['restaurant.table'].search(
            [('floor_id', '=', int(kwargs.get('floors_id')))])
        reserved = request.env['table.reservation'].search(
            [('floor_id', '=', int(kwargs.get('floors_id'))), (
                'date', '=', datetime.strptime(kwargs.get('date'),
                                               "%Y-%m-%d")), (
                'state', '=', 'reserved')])
        start_time_new = datetime.strptime(kwargs.get("start"), "%H:%M").time()
        for rec in reserved:
            start_at = datetime.strptime(rec.starting_at, "%H:%M").time()
            end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
            if start_at <= start_time_new <= end_at:
                for table in rec.booked_tables_ids:
                    table_inbetween.append(table.id)
        data_tables = {}
        for rec in tables:
            if rec.id not in table_inbetween:
                if payment:
                    data_tables[rec.id] = {}
                    data_tables[rec.id]['id'] = rec.id
                    data_tables[rec.id]['name'] = rec.name
                    data_tables[rec.id]['seats'] = rec.seats
                    data_tables[rec.id]['rate'] = rec.rate
                else:
                    data_tables[rec.id] = {}
                    data_tables[rec.id]['id'] = rec.id
                    data_tables[rec.id]['name'] = rec.name
                    data_tables[rec.id]['seats'] = rec.seats
                    data_tables[rec.id]['rate'] = 0
        return data_tables

    @http.route(['/booking/confirm'], type="http", auth="public",
                csrf=False, website=True)
    def booking_confirm(self, **kwargs):
        """For booking tables"""
        company = request.env.company
        list_tables = [rec for rec in kwargs.get("tables").split(',')]
        record_tables = request.env['restaurant.table'].search(
            [('id', 'in', list_tables)])
        amount = [rec.rate for rec in record_tables]
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        if payment:
            table = request.env.ref(
                'table_reservation_on_website'
                '.product_product_table_booking')
            table.write({
                'list_price': sum(amount)
            })
            sale_order = request.website.sale_get_order(force_create=True)
            if sale_order.state != 'draft':
                request.session['sale_order_id'] = None
                sale_order = request.website.sale_get_order(force_create=True)
            sale_order.sudo().write({
                'tables_ids': record_tables,
                'floors': kwargs.get('floors'),
                'date': kwargs.get('date'),
                'starting_at': kwargs.get('start_time'),
                "ending_at": kwargs.get('end_time'),
                'booking_amount': sum(amount),
                'order_line': [
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
            })
            sale_order.website_id = request.env['website'].search(
                [('company_id',
                  '=',
                  company.id)],
                limit=1)
            return request.redirect("/shop/cart")
        else:
            request.env['table.reservation'].sudo().create({
                "customer_id": request.env.user.partner_id.id,
                "booked_tables_ids": record_tables,
                "floor_id": kwargs.get('floors'),
                "date": kwargs.get('date'),
                "starting_at": kwargs.get('start_time'),
                "ending_at": kwargs.get('end_time'),
                'booking_amount': 0,
                'state': 'reserved',
            })
            return request.render(
                "table_reservation_on_website.table_reserved_template")

    @http.route(['/table/reservation/pos'], type='json', auth='user',
                website=True)
    def table_reservation_pos(self, partner_id, table_id):
        """For pos table booking"""
        table = request.env['restaurant.table'].browse(table_id)
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
                'customer_id': partner_id,
                'floor_id': table.floor_id.id,
                'booked_tables_ids': table,
                'date': date_and_time.date(),
                'starting_at': starting_at,
                'ending_at': end_time,
                'booking_amount': table.rate,
                'state': 'reserved',
            })
        else:
            request.env['table.reservation'].sudo().create({
                'customer_id': partner_id,
                'floor_id': table.floor_id.id,
                'booked_tables_ids': table,
                'date': date_and_time.date(),
                'starting_at': starting_at,
                'ending_at': end_time,
                'booking_amount': 0,
                'state': 'reserved',
            })
        return

    @http.route(['/active/floor/tables'], type='json', auth='user',
                website=True)
    def active_floor_tables(self, floor_id):
        """To get active floors"""
        table_inbetween = []
        table_reservation = request.env['table.reservation'].sudo().search([(
            'floor_id', "=", floor_id), ('date', '=', datetime.now().date()),
            ('state', '=', 'reserved')])
        for rec in table_reservation:
            start_at = datetime.strptime(rec.starting_at, "%H:%M").time()
            end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
            now = (
                (datetime.now() + timedelta(hours=5,
                                            minutes=30)).time()).strftime(
                "%H:%M")
            if start_at <= datetime.strptime(now, "%H:%M").time() <= end_at:
                for table in rec.booked_tables_ids:
                    table_inbetween.append(table.id)
        return table_inbetween
