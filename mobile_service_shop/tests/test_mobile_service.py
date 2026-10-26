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
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestMobileService(TransactionCase):
    """Test suite for mobile.service model (mobile_service.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Security groups
        cls.group_technician = cls.env.ref('mobile_service_shop.mobile_service_shop_group_user')
        cls.group_manager = cls.env.ref('mobile_service_shop.mobile_service_shop_group_manager')

        # Test users
        cls.tech_user = cls.env['res.users'].create({
            'name': 'Test Technician',
            'login': 'tech_user_svc_test',
            'email': 'tech_svc@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_technician.id])],
        })

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Service Manager',
            'login': 'manager_user_svc_test',
            'email': 'manager_svc@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_manager.id])],
        })

        # Test Customer
        cls.customer = cls.env['res.partner'].create({
            'name': 'Service Flow Customer',
            'email': 'service_cust@example.com',
        })

        # Brand and model
        cls.brand = cls.env['mobile.brand'].create({'brand_name': 'Motorola'})
        cls.model = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand.id,
            'mobile_brand_models': 'Moto G84',
        })

        # Part Product
        cls.part = cls.env['product.product'].create({
            'name': 'Moto Replacement Speaker',
            'is_storable': True,
            'is_a_parts': True,
            'list_price': 35.0,
        })

        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if cls.warehouse:
            location = cls.warehouse.lot_stock_id
            cls.env['stock.quant']._update_available_quantity(cls.part, location, 10)

    def test_01_service_creation_and_sequence(self):
        """Verify mobile.service creation generates sequence number correctly."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
            'technician_name': self.tech_user.id,
        })
        self.assertTrue(service.name)
        self.assertTrue(service.name.startswith('SERV/'))
        self.assertEqual(service.service_state, 'draft')

    def test_02_default_picking_and_journal_methods(self):
        """Verify _default_picking_transfer and _default_journal_type behave safely."""
        service = self.env['mobile.service'].new({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        picking_type = service._default_picking_transfer()
        if picking_type:
            self.assertTrue(hasattr(picking_type, 'id') or isinstance(picking_type, int))

        journal = service._default_journal_type()
        if journal:
            self.assertEqual(journal.type, 'sale')

    def test_03_return_date_onchange_validation(self):
        """Verify onchange raises UserError if return date is earlier than request date."""
        service = self.env['mobile.service'].new({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'date_request': fields.Date.today(),
            'return_date': fields.Date.today() - timedelta(days=1),
        })
        with self.assertRaises(UserError):
            service._onchange_return_date()

    def test_04_service_state_lifecycle(self):
        """Verify state transitions: draft -> assigned -> completed -> returned / not_solved."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
            'technician_name': self.tech_user.id,
        })
        self.assertEqual(service.service_state, 'draft')

        # Approve -> assigned
        service.action_approve()
        self.assertEqual(service.service_state, 'assigned')

        # Cannot delete assigned service
        with self.assertRaises(UserError):
            service.unlink()

        # Complete
        service.action_complete()
        self.assertEqual(service.service_state, 'completed')

        # Return to client
        service.action_return_to()
        self.assertEqual(service.service_state, 'returned')

        # Not solved state test on separate record
        service_unsolved = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        service_unsolved.action_not_solved()
        self.assertEqual(service_unsolved.service_state, 'not_solved')

    def test_05_ticket_report_action(self):
        """Verify action_get_ticket generates valid report action dictionary."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
            'technician_name': self.tech_user.id,
            'is_in_warranty': True,
            'warranty_number': 'WARR-7788',
        })
        action = service.action_get_ticket()
        self.assertIsInstance(action, dict)
        self.assertTrue(
            action.get('type') in ('ir.actions.report', 'ir.actions.act_window') or
            'report_action' in action.get('context', {})
        )

    def test_06_email_notification_handling(self):
        """Verify action_send_mail returns action or raises UserError if template missing."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        template = self.env.ref(
            'mobile_service_shop.email_template_mobile_service',
            raise_if_not_found=False,
        )
        if template:
            action = service.action_send_mail()
            self.assertIsInstance(action, dict)
            self.assertEqual(action.get('type'), 'ir.actions.act_window')

        # Remove template to verify UserError handling
        ir_model_data = self.env['ir.model.data'].search([
            ('module', '=', 'mobile_service_shop'),
            ('name', '=', 'email_template_mobile_service')
        ])
        if ir_model_data:
            template_record = self.env['mail.template'].browse(ir_model_data.res_id)
            ir_model_data.unlink()
            template_record.unlink()
            with self.assertRaises(UserError):
                service.action_send_mail()

    def test_07_stock_move_picking(self):
        """Verify action_post_stock creates picking, validates it, and updates quantities."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        order_line = self.env['product.order.line'].create({
            'product_order_id': service.id,
            'product_id': self.part.id,
            'product_uom': 'Units',
            'price_unit': 35.0,
            'product_uom_qty': 1.0,
        })
        service.action_post_stock()
        self.assertTrue(service.stock_picking_id)
        self.assertEqual(service.stock_picking_id.state, 'done')
        self.assertEqual(order_line.qty_stock_move, 1.0)
        self.assertTrue(order_line.stock_number)

    def test_08_action_return_advance_and_invoice_count(self):
        """Verify action_return_advance and invoice count calculations."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        # When no invoice exists, should raise UserError
        with self.assertRaises(UserError):
            service.action_return_advance()

        # Create invoice linked via invoice_origin
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_origin': service.name,
            'invoice_line_ids': [(0, 0, {
                'name': 'Service Item',
                'quantity': 1.0,
                'price_unit': 50.0,
            })],
        })
        service._compute_invoice_count()
        service._get_invoiced()
        self.assertEqual(service.invoice_count, 1)
        self.assertIn(inv.id, service.invoice_ids.ids)

        # Calling action_return_advance should return act_window
        action = service.action_return_advance()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_id'), inv.id)

    def test_09_technician_access_service_with_invoices(self):
        """Verify technician can read non-draft service with invoice
        stat button fields without AccessError."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
            'technician_name': self.tech_user.id,
        })
        service.action_approve()
        self.assertEqual(service.service_state, 'assigned')

        # Create linked invoice
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_origin': service.name,
            'invoice_line_ids': [(0, 0, {
                'name': 'Diagnostic Fee',
                'quantity': 1.0,
                'price_unit': 25.0,
            })],
        })

        # Technician reading the service record and invoice fields should not raise AccessError
        tech_service = service.with_user(self.tech_user)
        res = tech_service.read(['name', 'service_state', 'invoice_count', 'invoice_ids'])
        self.assertTrue(res)
        self.assertEqual(res[0]['invoice_count'], 1)

    def test_10_manager_user_action_post_stock(self):
        """Verify manager user can execute stock operations on mobile service."""
        service = self.env['mobile.service'].with_user(self.manager_user).create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
            'technician_name': self.tech_user.id,
        })
        self.env['product.order.line'].with_user(self.manager_user).create({
            'product_order_id': service.id,
            'product_id': self.part.id,
            'product_uom': 'Units',
            'price_unit': 35.0,
            'product_uom_qty': 1.0,
        })
        service.with_user(self.manager_user).action_post_stock()
        self.assertTrue(service.stock_picking_id)
        self.assertEqual(service.stock_picking_id.state, 'done')

