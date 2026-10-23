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
from odoo.tests.common import TransactionCase


class DeliveryTrackingCommon(TransactionCase):
    """Shared data for the website order delivery tracking tests."""

    API_KEY = 'test-api-key-123'
    API_KEY_PARAM = 'website_order_delivery_tracking.delivery_tracking_api_key'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_str(
            cls.API_KEY_PARAM, cls.API_KEY)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Tracking Test Customer',
        })
        cls.carrier_product = cls.env['product.product'].create({
            'name': 'Tracking Test Delivery',
            'type': 'service',
            'list_price': 5.0,
        })
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': 'Tracking Test Carrier',
            'delivery_type': 'fixed',
            'fixed_price': 5.0,
            'product_id': cls.carrier_product.id,
        })
        cls.picking = cls._create_picking(
            origin='S-TRACK-001', tracking_ref='TRACK-001')

    @classmethod
    def _create_picking(cls, origin=False, tracking_ref=False, carrier=True):
        """Create an outgoing picking, with an optional tracking reference."""
        picking_type = cls.env.ref('stock.warehouse0').out_type_id
        return cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': cls.env.ref(
                'stock.stock_location_customers').id,
            'origin': origin,
            'carrier_id': cls.carrier.id if carrier else False,
            'carrier_tracking_ref': tracking_ref,
        })
