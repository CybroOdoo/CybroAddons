# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


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
