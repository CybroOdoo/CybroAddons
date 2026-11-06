# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Henna Mehjabin (odoo@cybrosys.com)
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
################################################################################
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


@tagged('post_install', '-at_install')
class TestPortalDashboard(TransactionCase):
    """Test suite verifying portal dashboard data fetching, settings, and business logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Portal Customer Partner',
            'email': 'portal@test.com',
        })

        portal_group = cls.env.ref('base.group_portal')
        cls.portal_user = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'Portal User',
            'login': 'portaluser_test',
            'password': 'portaluser_test',
            'email': 'portal@test.com',
            'partner_id': cls.partner.id,
            'group_ids': [(4, portal_group.id)],
        })

        internal_group = cls.env.ref('base.group_user')
        billing_group = cls.env.ref('account.group_account_invoice')
        sales_group = cls.env.ref('sales_team.group_sale_salesman')
        purchase_group = cls.env.ref('purchase.group_purchase_user')
        cls.internal_user = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'Internal Staff User',
            'login': 'internaluser_test',
            'password': 'internaluser_test',
            'email': 'internal@test.com',
            'group_ids': [
                (4, internal_group.id),
                (4, billing_group.id),
                (4, sales_group.id),
                (4, purchase_group.id),
            ],
        })

    def test_config_settings_and_parameters(self):
        """Test configuration settings persistence and parameter storage."""
        settings = self.env['res.config.settings'].create({
            'is_show_recent_so_q': True,
            'sale_count': 10,
            'is_show_recent_po_rfq': True,
            'purchase_count': 8,
            'is_show_project': True,
            'project_count': 6,
            'is_show_recent_invoice_bill': True,
            'account_count': 4,
        })
        settings.execute()

        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(params.get_param('portal_dashboard.sale_count'), '10')
        self.assertEqual(params.get_param('portal_dashboard.purchase_count'), '8')
        self.assertEqual(params.get_param('portal_dashboard.project_count'), '6')
        self.assertEqual(params.get_param('portal_dashboard.account_count'), '4')
        self.assertEqual(params.get_param('portal_dashboard.is_show_recent_so_q'), 'True')

    def test_portal_user_datafetch_excludes_draft_records(self):
        """Verify portal customer datafetch includes sent quotes/RFQs and strictly excludes draft."""
        # 1 confirmed Sale Order
        self.env['sale.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'sale',
        })
        # 1 sent Quotation (visible to portal)
        self.env['sale.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'sent',
        })
        # 1 draft Quotation (MUST NOT be visible to portal customer)
        self.env['sale.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })

        # 1 confirmed Purchase Order
        self.env['purchase.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'purchase',
        })
        # 1 sent RFQ (visible to portal)
        self.env['purchase.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'sent',
        })
        # 1 draft RFQ (MUST NOT be visible to portal vendor)
        self.env['purchase.order'].sudo().create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })

        # 1 posted Customer Invoice
        cust_inv = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Invoice Line',
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        cust_inv.action_post()

        # 1 posted Vendor Bill
        vendor_bill = self.env['account.move'].sudo().create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Bill Line',
                'quantity': 1,
                'price_unit': 50.0,
            })],
        })
        vendor_bill.action_post()

        # Call datafetch as the portal user
        data = self.env['portal.dashboard.data'].with_user(self.portal_user).datafetch()

        self.assertIn('target', data)
        self.assertIn('target_po', data)
        self.assertIn('target_accounting', data)

        # Sales Analysis: [so_count, q_count] -> strictly sent/cancel, excluding draft
        self.assertEqual(data['target'][0], 1, "Should count 1 confirmed sales order")
        self.assertEqual(data['target'][1], 1, "Should count 1 sent quote and exclude draft quotes")

        # Purchase Analysis: [po_count, rfq_count] -> strictly sent/to approve, excluding draft
        self.assertEqual(data['target_po'][0], 1, "Should count 1 purchase order")
        self.assertEqual(data['target_po'][1], 1, "Should count 1 sent RFQ and exclude draft RFQs")

        # Accounting Analysis: [invoice_count, bill_count]
        self.assertEqual(data['target_accounting'][0], 1, "Should count 1 customer invoice")
        self.assertEqual(data['target_accounting'][1], 1, "Should count 1 vendor bill")

    def test_internal_staff_datafetch_by_salesperson_and_purchaser(self):
        """Verify internal staff datafetch includes records where staff is salesperson/purchaser."""
        other_partner = self.env['res.partner'].create({
            'name': 'Other Client Partner',
        })

        # Sales order assigned to internal user
        self.env['sale.order'].sudo().create({
            'partner_id': other_partner.id,
            'user_id': self.internal_user.id,
            'state': 'sale',
        })
        # Quotation assigned to internal user
        self.env['sale.order'].sudo().create({
            'partner_id': other_partner.id,
            'user_id': self.internal_user.id,
            'state': 'draft',
        })
        # Purchase order assigned to internal user
        self.env['purchase.order'].sudo().create({
            'partner_id': other_partner.id,
            'user_id': self.internal_user.id,
            'state': 'purchase',
        })
        # RFQ assigned to internal user
        self.env['purchase.order'].sudo().create({
            'partner_id': other_partner.id,
            'user_id': self.internal_user.id,
            'state': 'draft',
        })
        # Invoice where internal user is salesperson
        staff_inv = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': other_partner.id,
            'invoice_user_id': self.internal_user.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Staff Invoice Line',
                'quantity': 1,
                'price_unit': 120.0,
            })],
        })
        staff_inv.action_post()

        data = self.env['portal.dashboard.data'].with_user(self.internal_user).datafetch()

        self.assertGreaterEqual(data['target'][0], 1, "Staff should see sales order where they are salesperson")
        self.assertGreaterEqual(data['target'][1], 1, "Staff should see quotation where they are salesperson")
        self.assertGreaterEqual(data['target_po'][0], 1, "Staff should see purchase order where they are purchaser")
        self.assertGreaterEqual(data['target_po'][1], 1, "Staff should see RFQ where they are purchaser")
        self.assertGreaterEqual(data['target_accounting'][0], 1, "Staff should see invoice where they are salesperson")


@tagged('post_install', '-at_install')
class TestPortalDashboardHttp(HttpCase):
    """HTTP test cases verifying portal dashboard controller routes and rendering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        portal_group = cls.env.ref('base.group_portal')
        cls.portal_partner = cls.env['res.partner'].create({
            'name': 'HTTP Test Customer Partner',
            'email': 'portalhttp_test@test.com',
        })
        cls.portal_user = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'HTTP Portal User',
            'login': 'portaluserhttp_test',
            'password': 'portaluserhttp_test',
            'email': 'portalhttp_test@test.com',
            'partner_id': cls.portal_partner.id,
            'group_ids': [(4, portal_group.id)],
        })

    def test_portal_home_rendering(self):
        """Verify that /my loads the portal dashboard template successfully."""
        self.authenticate('portaluserhttp_test', 'portaluserhttp_test')
        response = self.url_open('/my')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'portal_dashboard', response.content)
        self.assertIn(b'Sales Orders', response.content)
        self.assertIn(b'Quotations', response.content)
        self.assertIn(b'sales_pie', response.content)
        self.assertIn(b'purchase_pie', response.content)
        self.assertIn(b'account_pie', response.content)

    def test_portal_standard_routes_accessible(self):
        """Verify standard portal routes remain fully accessible without interference."""
        self.authenticate('portaluserhttp_test', 'portaluserhttp_test')
        routes = ['/my/orders', '/my/quotes', '/my/rfq', '/my/purchase', '/my/projects', '/my/tasks', '/my/invoices']
        for route_url in routes:
            response = self.url_open(route_url)
            self.assertEqual(response.status_code, 200, f"Route {route_url} should return 200 OK")

    def test_internal_staff_invoice_filtration_matches(self):
        """Verify internal staff invoice count on /my matches records on /my/invoices?filterby=invoices."""
        internal_group = self.env.ref('base.group_user')
        billing_group = self.env.ref('account.group_account_invoice')
        staff_partner = self.env['res.partner'].create({
            'name': 'Staff HTTP Partner',
            'email': 'staffhttp@test.com',
        })
        staff_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Staff HTTP User',
            'login': 'staffhttp_test',
            'password': 'staffhttp_test',
            'email': 'staffhttp@test.com',
            'partner_id': staff_partner.id,
            'group_ids': [(4, internal_group.id), (4, billing_group.id)],
        })
        # 1 invoice assigned to staff
        inv1 = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.portal_partner.id,
            'invoice_user_id': staff_user.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {'name': 'Staff Line', 'quantity': 1, 'price_unit': 100.0})],
        })
        inv1.action_post()
        # 1 other invoice not assigned to staff
        other_partner = self.env['res.partner'].create({'name': 'Other Client Partner 2'})
        inv2 = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': other_partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {'name': 'Other Line', 'quantity': 1, 'price_unit': 200.0})],
        })
        inv2.action_post()

        self.authenticate('staffhttp_test', 'staffhttp_test')
        res_home = self.url_open('/my')
        self.assertEqual(res_home.status_code, 200)

        res_invoices = self.url_open('/my/invoices?filterby=invoices')
        self.assertEqual(res_invoices.status_code, 200)
        self.assertIn(inv1.name.encode(), res_invoices.content)
        self.assertNotIn(inv2.name.encode(), res_invoices.content)
