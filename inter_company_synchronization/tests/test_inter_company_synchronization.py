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
from unittest.mock import patch
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestInterCompanySynchronization(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env['res.company'].create({
            'name': 'Intercompany Test B',
        })
        cls.env.user.write({
            'company_ids': [Command.link(cls.company_b.id)],
        })
        cls.env = cls.env(user=cls.env.user, context=dict(
            cls.env.context,
            allowed_company_ids=[cls.company_a.id, cls.company_b.id],
        ))
        cls.company_a = cls.env['res.company'].browse(cls.company_a.id)
        cls.company_b = cls.env['res.company'].browse(cls.company_b.id)
        cls.product = cls.env['product.product'].create({
            'name': 'Intercompany synchronization product',
            'type': 'consu',
            'is_storable': True,
            'list_price': 25,
            'standard_price': 15,
        })
        cls.transit = cls.env.ref('stock.stock_location_inter_company')
        cls.transit.active = True
        cls.env['ir.config_parameter'].sudo().set_bool(
            'inter_company_synchronization.sale_purchase_sync', True,
        )

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_bool(
            'inter_company_synchronization.sale_purchase_sync', True,
        )

    def _sale_order(self, company=None, partner=None, client_order_ref=False,
                    with_lines=True):
        company = company or self.company_a
        partner = partner or self.company_b.partner_id
        values = {
            'company_id': company.id,
            'partner_id': partner.id,
            'client_order_ref': client_order_ref or False,
            'order_line': [],
        }
        if with_lines:
            values['order_line'] = [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 25,
            })]
        return self.env['sale.order'].create(values)

    def _purchase_order(self, company=None, partner=None, origin=False,
                        with_lines=True):
        company = company or self.company_a
        partner = partner or self.company_b.partner_id
        values = {
            'company_id': company.id,
            'partner_id': partner.id,
            'origin': origin or False,
            'order_line': [],
        }
        if with_lines:
            values['order_line'] = [Command.create({
                'product_id': self.product.id,
                'product_qty': 2,
                'price_unit': 15,
            })]
        return self.env['purchase.order'].create(values)

    def test_settings_field_persists_config_parameter(self):
        settings = self.env['res.config.settings'].create({
            'sale_purchase_sync': False,
        })
        settings.execute()
        self.assertFalse(self.env['ir.config_parameter'].sudo().get_bool(
            'inter_company_synchronization.sale_purchase_sync',
        ))

        self.env['res.config.settings'].create({
            'sale_purchase_sync': True,
        }).execute()
        self.assertTrue(self.env['ir.config_parameter'].sudo().get_bool(
            'inter_company_synchronization.sale_purchase_sync',
        ))

    def test_sale_line_conversion_handles_product_and_display_lines(self):
        order = self._sale_order(with_lines=False)
        product_line = self.env['sale.order.line'].new({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 4,
            'product_uom_id': self.product.uom_id.id,
            'name': 'Product line',
            'price_unit': 12.5,
        })
        section = self.env['sale.order.line'].new({
            'order_id': order.id,
            'display_type': 'line_section',
            'name': 'Section',
        })
        note = self.env['sale.order.line'].new({
            'order_id': order.id,
            'display_type': 'line_note',
            'name': 'Note',
        })

        self.assertEqual(order._get_po_line_vals(product_line), {
            'product_id': self.product.id,
            'name': 'Product line',
            'product_qty': 4,
            'uom_id': self.product.uom_id.id,
            'price_unit': 12.5,
        })
        self.assertEqual(order._get_po_line_vals(section), {
            'display_type': 'line_section',
            'name': 'Section',
            'product_qty': 0.0,
            'price_unit': 0.0,
        })
        self.assertEqual(order._get_po_line_vals(note)['display_type'], 'line_note')

    def test_purchase_line_conversion_handles_product_and_display_lines(self):
        order = self._purchase_order(with_lines=False)
        product_line = self.env['purchase.order.line'].new({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_qty': 3,
            'name': 'Purchase product line',
            'price_unit': 11,
        })
        section = self.env['purchase.order.line'].new({
            'order_id': order.id,
            'display_type': 'line_section',
            'name': 'Purchase section',
        })
        note = self.env['purchase.order.line'].new({
            'order_id': order.id,
            'display_type': 'line_note',
            'name': 'Purchase note',
        })

        self.assertEqual(order._get_so_line_vals(product_line), {
            'product_id': self.product.id,
            'name': 'Purchase product line',
            'product_uom_qty': 3,
            'price_unit': 11,
        })
        self.assertEqual(order._get_so_line_vals(section), {
            'display_type': 'line_section',
            'name': 'Purchase section',
        })
        self.assertEqual(order._get_so_line_vals(note)['display_type'], 'line_note')

    def test_sale_order_creates_counterpart_purchase_order(self):
        order = self._sale_order()
        order.write({'order_line': [Command.create({
            'display_type': 'line_section',
            'name': 'Order section',
        }), Command.create({
            'display_type': 'line_note',
            'name': 'Order note',
        })]})

        purchase = order._create_purchase_order()

        self.assertTrue(purchase)
        self.assertEqual(purchase.company_id, self.company_b)
        self.assertEqual(purchase.partner_id, self.company_a.partner_id)
        self.assertEqual(purchase.origin, order.name)
        product_lines = purchase.order_line.filtered(lambda line: line.product_id)
        self.assertEqual(len(product_lines), 1)
        self.assertEqual(product_lines.product_id, self.product)
        self.assertEqual(product_lines.product_qty, 2)
        self.assertEqual(product_lines.price_unit, 25)
        self.assertEqual(
            set(purchase.order_line.filtered('display_type').mapped('display_type')),
            {'line_section', 'line_note'},
        )

    def test_sale_order_without_matching_company_returns_false(self):
        order = self._sale_order(partner=self.env['res.partner'].create({
            'name': 'Unmapped intercompany partner',
        }))

        self.assertFalse(order._create_purchase_order())

    def test_purchase_order_creates_counterpart_sale_order(self):
        order = self._purchase_order(company=self.company_b,
                                     partner=self.company_a.partner_id)
        order.write({'order_line': [Command.create({
            'display_type': 'line_section',
            'name': 'Purchase section',
            'product_qty': 0,
        }), Command.create({
            'display_type': 'line_note',
            'name': 'Purchase note',
            'product_qty': 0,
        })]})

        sale = order._create_sale_order()

        self.assertTrue(sale)
        self.assertEqual(sale.company_id, self.company_a)
        self.assertEqual(sale.partner_id, self.company_b.partner_id)
        self.assertEqual(sale.client_order_ref, order.name)
        product_lines = sale.order_line.filtered(lambda line: line.product_id)
        self.assertEqual(len(product_lines), 1)
        self.assertEqual(product_lines.product_id, self.product)
        self.assertEqual(product_lines.product_uom_qty, 2)
        self.assertEqual(product_lines.price_unit, 15)
        self.assertEqual(
            set(sale.order_line.filtered('display_type').mapped('display_type')),
            {'line_section', 'line_note'},
        )

    def test_purchase_order_without_matching_company_returns_false(self):
        order = self._purchase_order(partner=self.env['res.partner'].create({
            'name': 'Unmapped purchase partner',
        }))

        self.assertFalse(order._create_sale_order())

    def test_sale_confirmation_syncs_only_without_client_reference(self):
        order = self._sale_order()
        order.action_confirm()

        purchase = self.env['purchase.order'].search([
            ('origin', '=', order.name),
            ('company_id', '=', self.company_b.id),
        ])
        self.assertEqual(len(purchase), 1)

        referenced_order = self._sale_order(client_order_ref='Already linked')
        referenced_order.action_confirm()
        self.assertFalse(self.env['purchase.order'].search([
            ('origin', '=', referenced_order.name),
            ('company_id', '=', self.company_b.id),
        ]))

    def test_purchase_confirmation_syncs_only_without_origin(self):
        order = self._purchase_order(company=self.company_b,
                                     partner=self.company_a.partner_id)
        order.button_confirm()

        sale = self.env['sale.order'].search([
            ('client_order_ref', '=', order.name),
            ('company_id', '=', self.company_a.id),
        ])
        self.assertEqual(len(sale), 1)

        referenced_order = self._purchase_order(
            company=self.company_b,
            partner=self.company_a.partner_id,
            origin='Already linked',
        )
        referenced_order.button_confirm()
        self.assertFalse(self.env['sale.order'].search([
            ('client_order_ref', '=', referenced_order.name),
            ('company_id', '=', self.company_a.id),
        ]))

    def test_confirmation_does_not_sync_when_setting_is_disabled(self):
        self.env['ir.config_parameter'].sudo().set_bool(
            'inter_company_synchronization.sale_purchase_sync', False,
        )
        sale = self._sale_order()
        purchase = self._purchase_order(company=self.company_b,
                                        partner=self.company_a.partner_id)

        sale.action_confirm()
        purchase.button_confirm()

        self.assertFalse(self.env['purchase.order'].search([
            ('origin', '=', sale.name),
            ('company_id', '=', self.company_b.id),
        ]))
        self.assertFalse(self.env['sale.order'].search([
            ('client_order_ref', '=', purchase.name),
            ('company_id', '=', self.company_a.id),
        ]))

    def test_confirmation_does_not_sync_without_transit_location(self):
        transit_model = type(self.env['stock.location'])
        order = self._sale_order()
        original_search = transit_model.search

        def search_without_transit(model, domain=None, *args, **kwargs):
            if domain == [('active', '=', True), ('usage', '=', 'transit')]:
                return model.browse()
            return original_search(model, domain, *args, **kwargs)

        with patch.object(transit_model, 'search', search_without_transit):
            order.action_confirm()

        self.assertFalse(self.env['purchase.order'].search([
            ('origin', '=', order.name),
            ('company_id', '=', self.company_b.id),
        ]))

