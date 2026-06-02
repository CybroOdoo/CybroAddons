# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResPartnerBlacklist(TransactionCase):

    def test_add_and_remove_blacklist(self):
        partner = self.env["res.partner"].create({
            "name": "Blacklist Test Customer",
        })

        partner.action_add_blacklist()
        self.assertTrue(partner.blacklisted)

        partner.action_remove_blacklist()
        self.assertFalse(partner.blacklisted)
