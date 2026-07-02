# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestMailchimpMailingList(TransactionCase):

    def test_compute_display_fields(self):
        record = self.env['mailchimp.mailing.list'].new({
            'unsubscribe_count': 12,
            'campaign_count': 5,
            'list_rating': 4,
            'member_count': 99,
            'click_rate': 7,
        })

        record._compute_unsubscribe_count_display()
        record._compute_campaign_count_display()
        record._compute_list_rating_display()
        record._compute_member_count_display()
        record._compute_click_rate_display()

        self.assertEqual(record.unsubscribe_count_display, 12)
        self.assertEqual(record.campaign_count_display, 5)
        self.assertEqual(record.list_rating_display, 4)
        self.assertEqual(record.member_count_display, 99)
        self.assertEqual(record.click_rate_display, 7)

    def test_action_import_returns_false(self):
        record = self.env['mailchimp.mailing.list'].new({})
        self.assertFalse(record.action_import())

