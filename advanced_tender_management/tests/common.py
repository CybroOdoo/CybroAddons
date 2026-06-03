# -*- coding: utf-8 -*-
import base64
from datetime import date, timedelta

from odoo import Command
from odoo.tests.common import TransactionCase


class TenderManagementTestCommon(TransactionCase):
    """Shared fixtures for advanced_tender_management tests."""

    @classmethod
    def _ensure_product_template_defaults(cls):
        """Handle DB-level NOT NULL customizations on unloaded fields."""
        cls.env.cr.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'product_template'
              AND column_name IN ('sale_line_warn', 'sale_line_warn_msg')
        """)
        column_meta = {
            row[0]: row[1]
            for row in cls.env.cr.fetchall()
        }
        if column_meta.get('sale_line_warn') == 'NO' and 'sale_line_warn' not in cls.env['product.template']._fields:
            cls.env.cr.execute("""
                ALTER TABLE product_template
                ALTER COLUMN sale_line_warn SET DEFAULT 'no-message'
            """)
        if column_meta.get('sale_line_warn_msg') == 'NO' and 'sale_line_warn_msg' not in cls.env['product.template']._fields:
            cls.env.cr.execute("""
                ALTER TABLE product_template
                ALTER COLUMN sale_line_warn_msg SET DEFAULT ''
            """)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_product_template_defaults()
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
            'uom_po_id': cls.uom_unit.id,
            'purchase_ok': True,
        }
        product_template_vals_2 = {
            'name': 'Tender Product 2',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
            'purchase_ok': True,
        }
        if 'sale_line_warn' in cls.env['product.template']._fields:
            product_template_vals_1['sale_line_warn'] = 'no-message'
            product_template_vals_2['sale_line_warn'] = 'no-message'
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
                    'attachment': base64.b64encode(b'tender-data'),
                    'filename': 'spec.txt',
                }),
            ],
        }
        vals.update(overrides)
        return vals

    @classmethod
    def create_tender(cls, **overrides):
        return cls.env['tender.management'].create(cls._tender_vals(**overrides))

    @classmethod
    def create_bid(cls, tender, vendor=None, qualification_stage='initial', prices=None):
        vendor = vendor or cls.vendor_1
        prices = prices or {
            cls.product_1.id: 10,
            cls.product_2.id: 20,
        }
        return cls.env['tender.bidding'].create({
            'vendor_id': vendor.id,
            'tender_id': tender.id,
            'qualification_stage': qualification_stage,
            'tender_bid_products_ids': [
                Command.create({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'display_type': line.display_type,
                    'product_price': 0 if line.display_type else prices.get(line.product_id.id, 0),
                })
                for line in tender.tender_product_line_ids
            ],
        })
