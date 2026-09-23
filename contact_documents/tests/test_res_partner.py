# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerDocuments(TransactionCase):
    """Tests for the contact document smart button behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Document Count Partner",
        })
        cls.other_partner = cls.env["res.partner"].create({
            "name": "Other Document Partner",
        })

    def _create_attachment(self, partner, name):
        return self.env["ir.attachment"].create({
            "name": name,
            "res_name": name,
            "type": "binary",
            "res_model": "res.partner",
            "res_id": partner.id,
            "datas": base64.b64encode(b"test attachment content"),
        })

    def test_compute_total_document_count_counts_partner_attachments(self):
        self._create_attachment(self.partner, "first.txt")
        self._create_attachment(self.partner, "second.txt")
        self._create_attachment(self.other_partner, "other.txt")

        (self.partner | self.other_partner)._compute_total_document_count()

        self.assertEqual(self.partner.document_count, "2")
        self.assertEqual(self.other_partner.document_count, "1")

    def test_action_partner_documents_returns_partner_attachment_action(self):
        action = self.partner.action_partner_documents()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["name"], "Documents")
        self.assertEqual(action["view_mode"], "kanban,form")
        self.assertEqual(action["res_model"], "ir.attachment")
        self.assertEqual(action["domain"], [
            ("res_id", "=", self.partner.id),
            ("res_model", "=", "res.partner"),
        ])
        self.assertEqual(action["context"], {"create": False})
