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
from psycopg2 import IntegrityError
from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestInvoiceTags(TransactionCase):

    def setUp(self):
        super().setUp()
        self.tag_model = self.env["invoice.tag"]

    def test_tag_defaults_and_unique_name(self):
        tag = self.tag_model.create({"name": "Services"})

        self.assertTrue(1 <= tag.color <= 11)
        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, IntegrityError)):
            self.tag_model.create({"name": "Services"})

    def test_tag_write_multiple_records(self):
        tags = self.tag_model.create([
            {"name": "TagA"},
            {"name": "TagB"},
        ])
        # Multi-record write must succeed without raising misleading error
        tags.write({"color": 5})
        self.assertEqual(tags.mapped("color"), [5, 5])

        # Renaming to existing name must raise constraint error
        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, IntegrityError)):
            tags[0].write({"name": "TagB"})
            tags.flush_recordset(['name'])

    def test_invoice_can_have_multiple_tags(self):
        tags = self.tag_model.create([
            {"name": "Consulting"},
            {"name": "Support"},
        ])
        partner = self.env["res.partner"].create({"name": "Invoice Tag Customer"})
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_tag_ids": [Command.set(tags.ids)],
        })

        self.assertEqual(invoice.invoice_tag_ids, tags)

    def test_search_invoice_by_tag(self):
        tag = self.tag_model.create({"name": "Searchable"})
        partner = self.env["res.partner"].create({"name": "Search Customer"})
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_tag_ids": [Command.set(tag.ids)],
        })
        other_invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
        })

        found_invoices = self.env["account.move"].search([("invoice_tag_ids", "in", tag.ids)])
        self.assertIn(invoice, found_invoices)
        self.assertNotIn(other_invoice, found_invoices)

    def test_tag_unlink(self):
        tag = self.tag_model.create({"name": "Temporary"})
        partner = self.env["res.partner"].create({"name": "Temp Customer"})
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_tag_ids": [Command.set(tag.ids)],
        })
        self.assertIn(tag, invoice.invoice_tag_ids)

        tag.unlink()
        self.assertFalse(self.tag_model.search([("name", "=", "Temporary")]))
        self.assertNotIn(tag, invoice.invoice_tag_ids)

