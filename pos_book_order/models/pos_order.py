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
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inherited model for pos order,all confirmed booking orders are converted
       as pos orders"""
    _inherit = 'pos.order'

    booking_ref_id = fields.Many2one(
        'book.order',
        help="Booked order reference for the pos order")
    is_booked = fields.Boolean(
        string='Is Booked Order',
        help="Flag indicating whether this order was from a booking")

    def _get_common_extra_data(self):
        """ Appends booking details to receipt extra data if the order
            is linked to a booked order.
            :return dict: Dictionary containing receipt extra data with booking info
        """
        res = super()._get_common_extra_data()
        if self.booking_ref_id:
            booking = self.booking_ref_id
            res['booking_info'] = {
                'name': booking.name,
                'phone': booking.phone or False,
                'note': booking.note or False,
                'pickup': str(booking.pickup_date) if booking.pickup_date else False,
                'deliver': str(booking.deliver_date) if booking.deliver_date else False,
                'address': booking.delivery_address or False,
            }
        return res

    @api.model
    def _process_order(self, order, existing_order):
        """ Override to link the booked order reference to the POS order
            and update the booked order status to confirmed.
            :param dict order: POS order values dictionary from the UI
            :param existing_order: Existing POS order record or False
            :return int: ID of the processed pos.order record
        """
        order.pop('is_booked', None)
        booked_data = order.pop('booked_data', None)
        booked_ref_id = order.get('booking_ref_id') or (booked_data and booked_data.get('id'))

        book_order = False
        if booked_ref_id:
            if isinstance(booked_ref_id, int):
                book_order = self.env['book.order'].browse(booked_ref_id)
            elif isinstance(booked_ref_id, str):
                book_order = self.env['book.order'].search([('name', '=', booked_ref_id)], limit=1)
            elif isinstance(booked_ref_id, dict) and booked_ref_id.get('id'):
                book_order = self.env['book.order'].browse(booked_ref_id['id'])

            if book_order and book_order.exists():
                order['booking_ref_id'] = book_order.id
                order['is_booked'] = True
            else:
                order.pop('booking_ref_id', None)

        pos_order_id = super()._process_order(order, existing_order)

        if book_order and book_order.exists():
            pos_order = self.browse(pos_order_id)
            if not pos_order.booking_ref_id:
                pos_order.write({'booking_ref_id': book_order.id, 'is_booked': True})
            book_order.write({'state': 'confirmed'})
        return pos_order_id

    @api.model
    def _order_fields(self, ui_order):
        """ Overriding to pass value of booked order ref to PoS order
            and mark the corresponding booked order as confirmed.
            :param dict ui_order: Dictionary containing UI order details
            :return dict: Processed order fields dictionary
        """
        order_fields = super()._order_fields(ui_order) if hasattr(super(), '_order_fields') else {}
        if ui_order.get('is_booked'):
            booked_id = ui_order.get('booking_ref_id') or ui_order.get('booked_data', {}).get('id')
            if isinstance(booked_id, int):
                order_fields['booking_ref_id'] = booked_id
            elif isinstance(booked_id, str):
                book_order = self.env['book.order'].search([('name', '=', booked_id)], limit=1)
                if book_order:
                    order_fields['booking_ref_id'] = book_order.id
            if order_fields.get('booking_ref_id'):
                self.env['book.order'].browse(order_fields['booking_ref_id']).write({'state': 'confirmed'})
        return order_fields
