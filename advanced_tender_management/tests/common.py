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
from datetime import date, timedelta

from odoo import Command
from odoo.tools import BinaryBytes
from odoo.tests import HttpCase, TransactionCase


class TenderDataMixin:
    """Shared fixtures for advanced_tender_management tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.email = 'company@example.com'
        cls.category = cls.env['tender.category'].create({
            'name': 'Infrastructure',
        })
        cls.country = cls.env.ref('base.in')
        cls.state = cls.env['res.country.state'].search(
            [('country_id', '=', cls.country.id)],
            limit=1,
        )
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        product_template_vals_1 = {
            'name': 'Tender Product 1',
            'uom_id': cls.uom_unit.id,
            'purchase_ok': True,
        }
        product_template_vals_2 = {
            'name': 'Tender Product 2',
            'uom_id': cls.uom_unit.id,
            'purchase_ok': True,
        }
        cls.product_template_1 = cls.env['product.template'].create(product_template_vals_1)
        cls.product_template_2 = cls.env['product.template'].create(product_template_vals_2)
        cls.product_1 = cls.product_template_1.product_variant_id
        cls.product_2 = cls.product_template_2.product_variant_id
        cls.vendor_1 = cls.env['res.partner'].create({
            'name': 'Vendor One',
            'email': 'vendor1@example.com',
            'is_vendor': True,
            'supplier_rank': 1,
            'tender_category_ids': [Command.link(cls.category.id)],
        })
        cls.vendor_2 = cls.env['res.partner'].create({
            'name': 'Vendor Two',
            'email': 'vendor2@example.com',
            'is_vendor': True,
            'supplier_rank': 1,
            'tender_category_ids': [Command.link(cls.category.id)],
        })

    @classmethod
    def _tender_vals(cls, **overrides):
        today = date.today()
        vals = {
            'name': 'Test Tender',
            'responsible_id': cls.env.user.id,
            'tender_start_date': today,
            'tender_end_date': today + timedelta(days=5),
            'bid_start_date': today + timedelta(days=1),
            'bid_end_date': today + timedelta(days=4),
            'description': '<p>Test tender</p>',
            'tender_category_id': cls.category.id,
            'tender_type': 'single_vendor',
            'address_street': 'Street 1',
            'address_city': 'Kochi',
            'address_country_id': cls.country.id,
            'address_state_id': cls.state.id,
            'tender_product_line_ids': [
                Command.create({
                    'name': cls.product_1.name,
                    'product_id': cls.product_1.id,
                    'product_qty': 3,
                }),
                Command.create({
                    'name': cls.product_2.name,
                    'product_id': cls.product_2.id,
                    'product_qty': 2,
                }),
            ],
            'tender_file_ids': [
                Command.create({
                    'name': 'Spec',
                    'attachment': BinaryBytes(b'tender-data'),
                    'filename': 'spec.txt',
                }),
            ],
        }
        vals.update(overrides)
        return vals

    @classmethod
    def create_tender(cls, **overrides):
        return cls.env['tender.management'].create(cls._tender_vals(**overrides))

    @staticmethod
    def call_route(method, *args, **kwargs):
        """Call a controller route without the HTTP response wrapper."""
        endpoint = getattr(method, 'original_endpoint', None)
        if endpoint is None:
            return method(*args, **kwargs)
        return endpoint(method.__self__, *args, **kwargs)

    @classmethod
    def create_bid(cls, tender, vendor=None, qualification_stage='initial', prices=None):
        vendor = vendor or cls.vendor_1
        prices = prices or {
            cls.product_1.id: 10,
            cls.product_2.id: 20,
        }
        Bidding = cls.env['tender.bidding']
        return Bidding.create({
            'vendor_id': vendor.id,
            'tender_id': tender.id,
            'qualification_stage': qualification_stage,
            'tender_bid_products_ids': Bidding._prepare_bid_line_commands(
                tender, {str(product_id): price for product_id, price in prices.items()}),
        })


class TenderManagementTestCommon(TenderDataMixin, TransactionCase):
    """Transaction test case with the tender fixtures."""


class TenderManagementHttpCommon(TenderDataMixin, HttpCase):
    """HTTP test case with the tender fixtures."""
