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
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged
from odoo.addons.vendor_portal_odoo.controllers.vendor_portal_odoo import RFQCustomerPortal
from werkzeug.utils import redirect as werkzeug_redirect


@tagged("post_install", "-at_install")
class TestVendorRFQ(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor_rfq_model = cls.env["vendor.rfq"]
        cls.vendor_model = cls.env["res.partner"]
        cls.quote_model = cls.env["vendor.quote.history"]
        cls.product_model = cls.env["product.product"]

    def _create_vendor(self, name):
        return self.vendor_model.create({
            "name": name,
            "is_registered": True,
            "email": f"{name.lower().replace(' ', '.')}@example.com",
        })

    def _create_rfq(self, **values):
        return self.vendor_rfq_model.create({
            "name": "New",
            "closing_date": fields.Date.today(),
            **values,
        })

    def _add_quote(self, rfq, vendor, price, delivery_date):
        return self.quote_model.create({
            "quote_id": rfq.id,
            "vendor_id": vendor.id,
            "quoted_price": price,
            "estimate_date": delivery_date,
        })

    def test_create_assigns_sequence_and_defaults(self):
        rfq = self._create_rfq()

        self.assertNotEqual(rfq.name, "New")
        self.assertTrue(rfq.name)
        self.assertEqual(rfq.state, "draft")
        self.assertEqual(rfq.company_id, self.env.company)
        self.assertEqual(rfq.currency_id, self.env.company.currency_id)
        self.assertEqual(rfq.quote_date, fields.Date.context_today(self.env.user))

    def test_status_actions_support_multiple_rfqs(self):
        rfqs = self._create_rfq() | self._create_rfq()

        rfqs.action_pending()
        self.assertEqual(set(rfqs.mapped("state")), {"pending"})

        rfqs.action_cancel()
        self.assertEqual(set(rfqs.mapped("state")), {"cancel"})

    def test_set_rfq_done_approves_lowest_quote(self):
        vendor_a = self._create_vendor("Vendor Price A")
        vendor_b = self._create_vendor("Vendor Price B")
        rfq = self._create_rfq(state="in_progress")
        self._add_quote(rfq, vendor_a, 250, fields.Date.today())
        self._add_quote(rfq, vendor_b, 180, fields.Date.today())
        self.env["ir.config_parameter"].sudo().set_str(
            "vendor_portal_odoo.rfq_done_based_on", "based_on_price"
        )

        self.vendor_rfq_model.set_rfq_done()

        self.assertEqual(rfq.state, "done")
        self.assertEqual(rfq.approved_vendor_id, vendor_b)

    def test_set_rfq_done_approves_earliest_delivery(self):
        vendor_later = self._create_vendor("Vendor Delivery Later")
        vendor_earlier = self._create_vendor("Vendor Delivery Earlier")
        today = fields.Date.today()
        rfq = self._create_rfq(state="in_progress")
        self._add_quote(rfq, vendor_later, 100, today + timedelta(days=5))
        self._add_quote(rfq, vendor_earlier, 300, today + timedelta(days=2))
        self.env["ir.config_parameter"].sudo().set_str(
            "vendor_portal_odoo.rfq_done_based_on",
            "based_on_delivery_time",
        )

        self.vendor_rfq_model.set_rfq_done()

        self.assertEqual(rfq.state, "done")
        self.assertEqual(rfq.approved_vendor_id, vendor_earlier)

    def test_set_rfq_done_skips_rfq_without_quotes_or_due_date(self):
        no_quotes = self._create_rfq(state="in_progress")
        not_due = self._create_rfq(
            state="in_progress",
            closing_date=fields.Date.today() + timedelta(days=1),
        )
        vendor = self._create_vendor("Vendor for Not Due RFQ")
        self._add_quote(not_due, vendor, 100, fields.Date.today())

        self.vendor_rfq_model.set_rfq_done()

        self.assertEqual(no_quotes.state, "in_progress")
        self.assertFalse(no_quotes.approved_vendor_id)
        self.assertEqual(not_due.state, "in_progress")
        self.assertFalse(not_due.approved_vendor_id)

    def test_set_rfq_done_multiple_rfqs_scopes_to_own_quotes(self):
        vendor_a = self._create_vendor("Vendor A")
        vendor_b = self._create_vendor("Vendor B")
        vendor_c = self._create_vendor("Vendor C")

        rfq_1 = self._create_rfq(state="in_progress")
        self._add_quote(rfq_1, vendor_a, 500, fields.Date.today())
        self._add_quote(rfq_1, vendor_b, 400, fields.Date.today())

        rfq_2 = self._create_rfq(state="in_progress")
        self._add_quote(rfq_2, vendor_c, 100, fields.Date.today())

        self.env["ir.config_parameter"].sudo().set_str(
            "vendor_portal_odoo.rfq_done_based_on", "based_on_price"
        )
        self.vendor_rfq_model.set_rfq_done()

        # RFQ 1 should select Vendor B (400), NOT Vendor C (100) from RFQ 2!
        self.assertEqual(rfq_1.approved_vendor_id, vendor_b)
        self.assertEqual(rfq_2.approved_vendor_id, vendor_c)

    def test_uom_id_defaults_from_product(self):
        product = self.product_model.create({
            "name": "Test Product",
        })
        rfq = self._create_rfq(product_id=product.id)
        self.assertEqual(rfq.uom_id, product.uom_id)

    def test_action_create_quotation_creates_purchase_order(self):
        product = self.product_model.create({
            "name": "Test PO Product",
        })
        vendor = self._create_vendor("Vendor PO")
        rfq = self._create_rfq(
            state="done",
            product_id=product.id,
            quantity=5.0,
            approved_vendor_id=vendor.id,
        )
        self._add_quote(rfq, vendor, 25.0, fields.Date.today() + timedelta(days=3))
        res = rfq.action_create_quotation()

        self.assertEqual(rfq.state, "order")
        self.assertTrue(rfq.order_id)
        self.assertEqual(rfq.order_id.partner_id, vendor)
        self.assertEqual(len(rfq.order_id.order_line), 1)
        line = rfq.order_id.order_line[0]
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.product_qty, 5.0)
        self.assertEqual(line.price_unit, 25.0)
        self.assertEqual(line.uom_id, rfq.uom_id)

    def test_register_vendor_wizard_creates_user_and_sends_email(self):
        vendor = self._create_vendor("New Vendor Portal")
        wizard = self.env["register.vendor"].with_context(
            active_model="res.partner",
            active_id=vendor.id,
        ).create({})
        wizard.action_create_user_portal()
        user = self.env["res.users"].search([("partner_id", "=", vendor.id)])
        self.assertTrue(user)
        self.assertTrue(vendor.is_registered)

    def test_create_supports_single_dict_and_batch_list(self):
        product = self.product_model.create({"name": "Batch Product"})
        # Single dict create (previously broke with @api.model)
        single = self.vendor_rfq_model.create({
            "name": "New",
            "product_id": product.id,
        })
        self.assertTrue(single.name)
        self.assertNotEqual(single.name, "New")
        self.assertEqual(single.uom_id, product.uom_id)

        # Batch list create
        batch = self.vendor_rfq_model.create([
            {"name": "New", "product_id": product.id},
            {"name": "New", "product_id": product.id},
        ])
        self.assertEqual(len(batch), 2)
        self.assertNotEqual(batch[0].name, batch[1].name)
        self.assertEqual(batch.mapped("uom_id"), product.uom_id | product.uom_id)

    def test_set_rfq_done_handles_past_closing_date_and_default_order(self):
        vendor = self._create_vendor("Vendor Overdue")
        past_rfq = self._create_rfq(
            state="in_progress",
            closing_date=fields.Date.today() - timedelta(days=2),
        )
        self._add_quote(past_rfq, vendor, 120, fields.Date.today())
        # Ensure default sorting is price even if config parameter is missing
        self.env["ir.config_parameter"].sudo().search([
            ("key", "=", "vendor_portal_odoo.rfq_done_based_on")
        ]).unlink()

        self.vendor_rfq_model.set_rfq_done()
        self.assertEqual(past_rfq.state, "done")
        self.assertEqual(past_rfq.approved_vendor_id, vendor)

    def test_action_send_by_mail(self):
        vendor_1 = self._create_vendor("Mail Vendor 1")
        vendor_2 = self._create_vendor("Mail Vendor 2")
        rfq = self._create_rfq(
            state="draft",
            vendor_ids=[(6, 0, [vendor_1.id, vendor_2.id])],
        )
        sent_partner_ids = []
        orig_send_mail = type(self.env["mail.template"]).send_mail

        def mock_send_mail(tpl_self, *args, **kwargs):
            sent_partner_ids.append(tpl_self.env.context.get("partner_to"))
            return orig_send_mail(tpl_self, *args, **kwargs)

        with patch.object(type(self.env["mail.template"]), "send_mail", side_effect=mock_send_mail, autospec=True):
            rfq.action_send_by_mail()

        self.assertEqual(rfq.state, "in_progress")
        self.assertEqual(set(sent_partner_ids), {vendor_1.id, vendor_2.id})

    def test_rfq_done_wizard(self):
        vendor_a = self._create_vendor("Wizard Vendor A")
        vendor_b = self._create_vendor("Wizard Vendor B")
        rfq = self._create_rfq(state="in_progress")
        quote_a = self._add_quote(rfq, vendor_a, 200, fields.Date.today())
        quote_b = self._add_quote(rfq, vendor_b, 150, fields.Date.today())

        wizard = self.env["rfq.done"].with_context(
            active_id=rfq.id,
            default_quote_ids=rfq.vendor_quote_history_ids.ids,
        ).create({
            "vendor_id": quote_b.id,
            "quote_ids": [(6, 0, rfq.vendor_quote_history_ids.ids)],
        })
        done_partner_ids = []
        orig_send_mail = type(self.env["mail.template"]).send_mail

        def mock_done_send_mail(tpl_self, *args, **kwargs):
            done_partner_ids.append(tpl_self.env.context.get("partner_to"))
            return orig_send_mail(tpl_self, *args, **kwargs)

        with patch.object(type(self.env["mail.template"]), "send_mail", side_effect=mock_done_send_mail, autospec=True):
            wizard.action_done()

        self.assertEqual(rfq.state, "done")
        self.assertEqual(rfq.approved_vendor_id, vendor_b)
        self.assertEqual(done_partner_ids, [vendor_b.id])

    def test_quote_details_controller_state_check(self):
        vendor = self._create_vendor("State Check Vendor")
        product = self.product_model.create({"name": "State Check Product"})
        rfq = self._create_rfq(
            state="in_progress",
            product_id=product.id,
            vendor_ids=[(6, 0, [vendor.id])],
        )
        controller = RFQCustomerPortal()
        fake_req = MagicMock()
        fake_req.env.user.partner_id = vendor
        fake_req.env.__getitem__.side_effect = lambda model: self.env[model]
        fake_req.redirect.side_effect = lambda url: werkzeug_redirect(url)

        with patch("odoo.addons.vendor_portal_odoo.controllers.vendor_portal_odoo.request", fake_req):
            # 1. Vendor submits quote while in_progress -> should succeed
            res = controller.quote_details(rfq_id=str(rfq.id), price="100.0", delivery_date=str(fields.Date.today()))
            self.assertEqual(res.headers.get("Location"), f"/my/vendor_rfq/{rfq.id}")
            quote = self.quote_model.search([("quote_id", "=", rfq.id), ("vendor_id", "=", vendor.id)])
            self.assertEqual(quote.quoted_price, 100.0)

            # 2. RFQ is marked as done / awarded
            rfq.write({"state": "done", "approved_vendor_id": vendor.id})

            # 3. Vendor attempts to overwrite quoted_price after RFQ is done -> blocked
            res = controller.quote_details(rfq_id=str(rfq.id), price="999.0", delivery_date=str(fields.Date.today()))
            self.assertEqual(res.headers.get("Location"), f"/my/vendor_rfq/{rfq.id}")
            quote.invalidate_recordset()
            self.assertEqual(quote.quoted_price, 100.0)

            # 4. RFQ action_create_quotation takes original approved price into PO
            rfq.action_create_quotation()
            self.assertEqual(rfq.order_id.order_line[0].price_unit, 100.0)

            # 5. When state is order, vendor still cannot overwrite
            res = controller.quote_details(rfq_id=str(rfq.id), price="555.0")
            self.assertEqual(res.headers.get("Location"), f"/my/vendor_rfq/{rfq.id}")
            quote.invalidate_recordset()
            self.assertEqual(quote.quoted_price, 100.0)

    def test_get_purchase_order_action(self):
        product = self.product_model.create({"name": "PO Action Product"})
        vendor = self._create_vendor("Vendor PO Action")
        rfq = self._create_rfq(
            state="done",
            product_id=product.id,
            approved_vendor_id=vendor.id,
        )
        self._add_quote(rfq, vendor, 50.0, fields.Date.today())
        rfq.action_create_quotation()
        action = rfq.get_purchase_order()
        self.assertEqual(action.get("res_model"), "purchase.order")
        self.assertEqual(action.get("res_id"), rfq.order_id.id)

    def test_send_password_reset_portal(self):
        vendor = self._create_vendor("Reset Vendor")
        wizard = self.env["register.vendor"].with_context(
            active_model="res.partner",
            active_id=vendor.id,
        ).create({})
        wizard.action_create_user_portal()
        wizard.send_password_reset_portal()
        self.assertTrue(vendor.is_registered)

    def test_portal_counters_and_controller_logic(self):
        vendor = self._create_vendor("Portal Logic Vendor")
        rfq = self._create_rfq(
            state="in_progress",
            vendor_ids=[(6, 0, [vendor.id])],
        )
        controller = RFQCustomerPortal()

        fake_req = MagicMock()
        fake_req.env.user.partner_id = vendor
        fake_req.env.user.has_group.return_value = False
        fake_req.env.__getitem__.side_effect = lambda model: self.env[model]

        with patch('odoo.addons.vendor_portal_odoo.controllers.vendor_portal_odoo.request', fake_req):
            model, domain, sudo = controller._prepare_portal_counter_values('my_rfq_count')
            self.assertEqual(model, 'vendor.rfq')
            count = fake_req.env[model].sudo().search_count(domain)
            self.assertEqual(count, 1)

            values = controller._prepare_home_portal_values({})
            self.assertEqual(values.get('my_rfq_count'), 1)

    def test_res_config_settings_set_and_get_values(self):
        settings = self.env["res.config.settings"].create({
            "rfq_done_based_on": "based_on_delivery_time",
            "quote_submission_msg": "Custom submission message",
            "quote_accept_msg": "Custom accept message",
            "quote_not_accept_msg": "Custom not accept message",
            "quote_cancel_msg": "Custom cancel message",
            "quote_to_po_msg": "Custom PO message",
        })
        with patch('odoo.addons.base.models.ir_ui_view.IrUiView._check_xml'):
            settings.set_values()
        values = settings.get_values()
        self.assertEqual(values["rfq_done_based_on"], "based_on_delivery_time")
        self.assertEqual(values["quote_submission_msg"], "Custom submission message")
        self.assertEqual(values["quote_accept_msg"], "Custom accept message")
        self.assertEqual(values["quote_not_accept_msg"], "Custom not accept message")
        self.assertEqual(values["quote_cancel_msg"], "Custom cancel message")
        self.assertEqual(values["quote_to_po_msg"], "Custom PO message")


@tagged("post_install", "-at_install")
class TestVendorRFQPortalHttp(HttpCase):

    def test_portal_rfq_routes(self):
        portal_user = new_test_user(
            self.env,
            login="http_vendor_user",
            groups="base.group_portal",
            name="HTTP Portal Vendor",
            password="password123",
        )
        portal_partner = portal_user.partner_id
        portal_partner.write({
            "is_registered": True,
        })

        rfq = self.env["vendor.rfq"].create({
            "name": "New",
            "state": "in_progress",
            "vendor_ids": [(6, 0, [portal_partner.id])],
        })

        self.authenticate(portal_user.login, "password123")

        # 1. Access RFQs list
        res = self.url_open("/my/vendor_rfqs")
        self.assertEqual(res.status_code, 200)

        # 2. Access RFQ details
        res = self.url_open(f"/my/vendor_rfq/{rfq.id}")
        self.assertEqual(res.status_code, 200)

        # 3. Submit quote
        post_data = {
            "csrf_token": self.csrf_token(),
            "rfq_id": str(rfq.id),
            "price": "99.50",
            "delivery_date": str(fields.Date.today() + timedelta(days=5)),
            "additional_note": "HTTP test quote",
        }
        res = self.url_open("/quote/details", data=post_data)
        self.assertEqual(res.status_code, 200)

        quote = self.env["vendor.quote.history"].search([
            ("quote_id", "=", rfq.id),
            ("vendor_id", "=", portal_partner.id),
        ])
        self.assertTrue(quote)
        self.assertEqual(quote.quoted_price, 99.50)

        # 4. Attempt to overwrite quote after RFQ is done / awarded
        rfq.write({"state": "done", "approved_vendor_id": portal_partner.id})
        overwrite_post_data = {
            "csrf_token": self.csrf_token(),
            "rfq_id": str(rfq.id),
            "price": "9999.00",
            "delivery_date": str(fields.Date.today() + timedelta(days=5)),
            "additional_note": "Attempt to overwrite price after done",
        }
        res = self.url_open("/quote/details", data=overwrite_post_data)
        self.assertEqual(res.status_code, 200)

        quote.invalidate_recordset()
        # Price must NOT be overwritten
        self.assertEqual(quote.quoted_price, 99.50)
