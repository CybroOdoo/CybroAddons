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
from odoo.tests import common, tagged
from odoo import fields
from dateutil.relativedelta import relativedelta

@tagged('post_install', '-at_install')
class TestWarranty(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.product = self.env['product.product'].create({
            'name': 'Warranty Product',
            'is_warranty_available': True,
            'warranty_duration': 12,
            'warranty_period_type': 'months',
            'warranty_type': 'full',
            'list_price': 100.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })]
        })

    def test_01_warranty_generation_on_confirm(self):
        """ Test that is_warranty_check is set on sale order confirm"""
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.is_warranty_check, "Warranty check should be true")

    def test_02_manual_warranty_registration(self):
        """ Test manual generation of warranty registration via smart tab action"""
        self.sale_order.action_confirm()
        self.sale_order.action_open_smart_tab()
        
        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(registration, "Warranty registration should be created")
        self.assertEqual(registration.warranty_type, 'full')
        
        # Check expiry date (12 months)
        expected_expiry = fields.Date.context_today(self.sale_order) + relativedelta(months=12)
        self.assertEqual(registration.expiry_date, expected_expiry)

    def test_03_flexible_periods(self):
        """ Test different warranty periods (Days, Years)"""
        product_days = self.env['product.product'].create({
            'name': 'Days Product',
            'is_warranty_available': True,
            'warranty_duration': 30,
            'warranty_period_type': 'days',
        })
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product_days.id,
                'product_uom_qty': 1,
            })]
        })
        so.action_confirm()
        so.action_open_smart_tab()
        
        reg = self.env['warranty.registration'].search([('sale_order_id', '=', so.id)])
        expected_expiry = fields.Date.context_today(so) + relativedelta(days=30)
        self.assertEqual(reg.expiry_date, expected_expiry)

    def test_04_automatic_generation_on_delivery(self):
        """ Test that warranty is generated when delivery is validated """
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids[0]
        # Set quantities
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        
        picking.button_validate()
        
        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(registration, "Warranty registration should be automatically created on delivery")

    def test_smart_tab_does_not_duplicate_registrations(self):
        """Opening the registrations action repeatedly should be idempotent."""
        self.sale_order.action_confirm()

        first_action = self.sale_order.action_open_smart_tab()
        second_action = self.sale_order.action_open_smart_tab()

        registrations = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id),
        ])
        self.assertEqual(first_action['res_model'], 'warranty.registration')
        self.assertEqual(second_action['domain'], first_action['domain'])
        self.assertEqual(len(registrations), 1)

    def test_year_warranty_period_expiry_date(self):
        """Warranty duration expressed in years should set the correct expiry."""
        product = self.env['product.product'].create({
            'name': 'Years Product',
            'is_warranty_available': True,
            'warranty_duration': 2,
            'warranty_period_type': 'years',
            'warranty_type': 'reparable',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
            })],
        })

        order.action_open_smart_tab()

        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', order.id),
            ('product_id', '=', product.id),
        ])
        start_date = fields.Date.context_today(order)
        self.assertEqual(registration.start_date, start_date)
        self.assertEqual(registration.expiry_date,
                         start_date + relativedelta(years=2))
        self.assertEqual(registration.warranty_type, 'reparable')

    def test_registration_state_tracks_expiry_and_preserves_cancelled(self):
        """Expired dates update state while cancelled registrations stay cancelled."""
        today = fields.Date.context_today(self.sale_order)
        registration = self.env['warranty.registration'].create({
            'customer_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
            'expiry_date': today,
            'state': 'active',
        })
        self.assertEqual(registration.state, 'active')

        registration.expiry_date = today - relativedelta(days=1)
        self.assertEqual(registration.state, 'expired')

        registration.state = 'cancel'
        registration.expiry_date = today + relativedelta(days=30)
        self.assertEqual(registration.state, 'cancel')

    def test_claim_approval_and_rejection_actions(self):
        """Claim status actions should move draft claims to their final states."""
        approved_claim = self.env['warranty.claim'].create({
            'customer_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
        })
        rejected_claim = self.env['warranty.claim'].create({
            'customer_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
        })

        self.assertEqual(approved_claim.state, 'draft')
        self.assertEqual(rejected_claim.state, 'draft')
        approved_claim.change_status_approved()
        rejected_claim.change_status_rejected()

        self.assertEqual(approved_claim.state, 'approved')
        self.assertEqual(rejected_claim.state, 'rejected')

    def test_multi_record_action_confirm(self):
        """ Test action_confirm correctly sets is_warranty_check for multi-record sets"""
        product_no_warranty = self.env['product.product'].create({
            'name': 'No Warranty Product',
            'is_warranty_available': False,
        })
        so_no_warranty = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product_no_warranty.id,
                'product_uom_qty': 1,
            })]
        })
        orders = self.sale_order | so_no_warranty
        res = orders.action_confirm()
        self.assertTrue(res, "action_confirm must return super() result")
        self.assertTrue(self.sale_order.is_warranty_check)
        self.assertFalse(so_no_warranty.is_warranty_check)

    def test_smart_tab_ensure_one(self):
        """ Test that action_open_smart_tab raises error on multi-record set """
        self.sale_order.action_confirm()
        so2 = self.sale_order.copy()
        with self.assertRaises(Exception):
            (self.sale_order | so2).action_open_smart_tab()

    def test_claim_description_field(self):
        """ Test that description field is stored on warranty.claim """
        claim = self.env['warranty.claim'].create({
            'customer_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
            'description': 'Screen flickering issue',
        })
        self.assertEqual(claim.description, 'Screen flickering issue')

    def test_delivery_email_only_sent_once(self):
        """ Test that picking validation sends confirmation email only once per registration """
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids[0]
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()
        registration = self.env['warranty.registration'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(registration.is_email_sent)
        initial_messages = len(registration.message_ids)

        # Calling send confirmation email again should not post duplicate messages
        registration.action_send_confirmation_email()
        self.assertEqual(len(registration.message_ids), initial_messages)


from unittest.mock import MagicMock, patch
from werkzeug.utils import redirect
from odoo.addons.website_warranty_management.controllers.website_warranty_management import WarrantyClaimController
from odoo.addons.website_warranty_management.controllers.portal import PortalAccount


@tagged('post_install', '-at_install')
class TestWarrantyController(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.portal_partner = self.env['res.partner'].create({
            'name': 'Portal Customer',
            'email': 'portal_ctrl@example.com',
        })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Customer',
            'email': 'other_ctrl@example.com',
        })
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user_ctrl_test',
            'email': 'portal_ctrl@example.com',
            'partner_id': self.portal_partner.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Controller Warranty Product',
            'is_warranty_available': True,
            'warranty_duration': 6,
            'warranty_period_type': 'months',
            'warranty_type': 'full',
            'list_price': 50.0,
        })
        self.non_warranty_product = self.env['product.product'].create({
            'name': 'Non Warranty Product',
            'is_warranty_available': False,
            'list_price': 20.0,
        })
        self.unrelated_product = self.env['product.product'].create({
            'name': 'Unrelated Product',
            'is_warranty_available': True,
            'warranty_duration': 6,
            'list_price': 30.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'user_id': self.env.user.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.non_warranty_product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.sale_order.action_confirm()

        self.other_sale_order = self.env['sale.order'].create({
            'partner_id': self.other_partner.id,
            'user_id': self.env.user.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })
        self.other_sale_order.action_confirm()

    def test_claim_submit_ownership_and_description(self):
        """ Test warranty claim submit enforces ownership and stores description """
        controller = WarrantyClaimController()
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.portal_user)
        mock_req.render = MagicMock(return_value='claim_thanks')
        mock_req.redirect = MagicMock(side_effect=lambda url: redirect(url, code=303))

        with patch('odoo.addons.website_warranty_management.controllers.website_warranty_management.request', mock_req):
            # 1. Valid claim for owned sale order and warranty eligible product
            res = controller.warranty_claim_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.product.id),
                additional_field='Battery overheating issue',
            )
            self.assertEqual(res.status_code, 200)
            claim = self.env['warranty.claim'].search([
                ('sale_order_id', '=', self.sale_order.id),
                ('product_id', '=', self.product.id)
            ], limit=1)
            self.assertTrue(claim)
            self.assertEqual(claim.customer_id.id, self.portal_partner.id)
            self.assertEqual(claim.description, 'Battery overheating issue')

            # 2. Attack: trying to submit claim for other customer's order
            res_attack = controller.warranty_claim_submit(
                sale_order_id=str(self.other_sale_order.id),
                products_id=str(self.product.id),
                additional_field='Fake claim',
            )
            self.assertIn(res_attack.status_code, (302, 303))
            self.assertIn('/warranty', res_attack.headers.get('Location'))

            # 3. Attack: product not on sale order
            res_unrelated = controller.warranty_claim_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.unrelated_product.id),
                additional_field='Unrelated product claim',
            )
            self.assertIn(res_unrelated.status_code, (302, 303))
            self.assertIn('/warranty', res_unrelated.headers.get('Location'))

            # 4. Attack: product on order but not warranty eligible
            res_ineligible = controller.warranty_claim_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.non_warranty_product.id),
                additional_field='Ineligible product claim',
            )
            self.assertIn(res_ineligible.status_code, (302, 303))
            self.assertIn('/warranty', res_ineligible.headers.get('Location'))

    def test_register_submit_ownership(self):
        """ Test warranty register submit verifies ownership and product eligibility """
        controller = WarrantyClaimController()
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.portal_user)
        mock_req.render = MagicMock(return_value='reg_thanks')
        mock_req.redirect = MagicMock(side_effect=lambda url: redirect(url, code=303))

        with patch('odoo.addons.website_warranty_management.controllers.website_warranty_management.request', mock_req):
            # 1. Valid registration
            res = controller.warranty_register_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.product.id),
                serial_no='SN-12345',
            )
            self.assertEqual(res.status_code, 200)
            reg = self.env['warranty.registration'].search([
                ('sale_order_id', '=', self.sale_order.id),
                ('product_id', '=', self.product.id)
            ], limit=1)
            self.assertTrue(reg)
            self.assertEqual(reg.customer_id.id, self.portal_partner.id)
            self.assertEqual(reg.serial_no, 'SN-12345')

            # 2. Attack: unowned sale order
            res_attack = controller.warranty_register_submit(
                sale_order_id=str(self.other_sale_order.id),
                products_id=str(self.product.id),
                serial_no='SN-ATTACK',
            )
            self.assertIn(res_attack.status_code, (302, 303))
            self.assertIn('/warranty/register', res_attack.headers.get('Location'))

            # 3. Attack: product not on sale order
            res_unrelated = controller.warranty_register_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.unrelated_product.id),
                serial_no='SN-UNRELATED',
            )
            self.assertIn(res_unrelated.status_code, (302, 303))
            self.assertIn('/warranty/register', res_unrelated.headers.get('Location'))

            # 4. Attack: product not warranty eligible
            res_ineligible = controller.warranty_register_submit(
                sale_order_id=str(self.sale_order.id),
                products_id=str(self.non_warranty_product.id),
                serial_no='SN-INELIGIBLE',
            )
            self.assertIn(res_ineligible.status_code, (302, 303))
            self.assertIn('/warranty/register', res_ineligible.headers.get('Location'))

    def test_renewal_controller_route(self):
        """ Test renewal route with integer id and ownership verification """
        controller = WarrantyClaimController()
        registration = self.env['warranty.registration'].create({
            'customer_id': self.portal_partner.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
            'expiry_date': fields.Date.context_today(self.sale_order) + relativedelta(months=6),
            'state': 'active',
        })
        other_registration = self.env['warranty.registration'].create({
            'customer_id': self.other_partner.id,
            'sale_order_id': self.other_sale_order.id,
            'product_id': self.product.id,
            'expiry_date': fields.Date.context_today(self.other_sale_order) + relativedelta(months=6),
            'state': 'active',
        })

        mock_req = MagicMock()
        mock_req.env = self.env(user=self.portal_user)
        mock_req.render = MagicMock(return_value='renewal_thanks')
        mock_req.redirect = MagicMock(side_effect=lambda url: redirect(url, code=303))

        with patch('odoo.addons.website_warranty_management.controllers.website_warranty_management.request', mock_req):
            # 1. Valid renewal request for own registration
            res = controller.warranty_renewal(registration.id)
            self.assertEqual(res.status_code, 200)
            claim = self.env['warranty.claim'].search([
                ('warranty_registration_id', '=', registration.id),
                ('claim_type', '=', 'renewal')
            ])
            self.assertTrue(claim)

            # 2. Attack: requesting renewal for someone else's registration
            res_attack = controller.warranty_renewal(other_registration.id)
            self.assertIn(res_attack.status_code, (302, 303))
            self.assertIn('/my/claims', res_attack.headers.get('Location'))

    def test_portal_counter_hook(self):
        """ Test portal counter values hook returns correct model, domain, and sudo access """
        portal_ctrl = PortalAccount()
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.portal_user)

        with patch('odoo.addons.website_warranty_management.controllers.portal.request', mock_req):
            model, domain, access = portal_ctrl._prepare_portal_counter_values('claim_count')
            self.assertEqual(model, 'warranty.claim')
            self.assertEqual(access, 'sudo')
            self.assertIn(('customer_id', '=', self.portal_partner.id), domain)

            model_reg, domain_reg, access_reg = portal_ctrl._prepare_portal_counter_values('registration_count')
            self.assertEqual(model_reg, 'warranty.registration')
            self.assertEqual(access_reg, 'sudo')
