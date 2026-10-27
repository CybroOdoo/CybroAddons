# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveBarcode(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_journal = cls.env["account.journal"].create({
            "name": "Test Sales Journal",
            "code": "TSJ",
            "type": "sale",
        })

    def test_generate_ean_returns_valid_length_and_checksum(self):
        move_model = self.env["account.move"]

        ean = move_model.generate_ean("ABC-123")

        self.assertEqual(len(ean), 13)
        self.assertTrue(ean.isdigit())
        self.assertEqual(int(ean[-1]), move_model.ean_checksum(ean))

    def test_create_assigns_account_barcode(self):
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "journal_id": self.sale_journal.id,
        })

        self.assertTrue(move.account_barcode)
        self.assertEqual(len(move.account_barcode), 13)

    def test_ean_checksum_rejects_wrong_length(self):
        self.assertEqual(self.env["account.move"].ean_checksum("123"), -1)

    def test_check_ean_validates_generated_barcode(self):
        move_model = self.env["account.move"]
        self.assertTrue(move_model.check_ean(""))
        self.assertTrue(move_model.check_ean(move_model.generate_ean("42")))
        self.assertFalse(move_model.check_ean("123"))
        self.assertFalse(move_model.check_ean("ABCDEFGHIJKLM"))
