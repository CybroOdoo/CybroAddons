# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.website_customer_note.controllers.website_customer_note import (
    WebsiteSaleCustomerNote,
)


@tagged('-at_install', 'post_install')
class TestWebsiteCustomerNoteController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSaleCustomerNote()

    def _make_request(self):
        return SimpleNamespace(
            env=self.env,
        )

    def test_save_customer_note_requires_order_id(self):
        result = self.controller.save_customer_note(order_id=None, customer_note='Note')

        assert result == {'success': False, 'error': 'No order_id provided'}

    def test_save_customer_note_updates_existing_order(self):
        order = MagicMock()
        order.exists.return_value = True
        fake_env = MagicMock()
        fake_env.__getitem__.return_value.sudo.return_value.browse.return_value = order
        fake_request = self._make_request()
        fake_request.env = fake_env

        with patch(
            'odoo.addons.website_customer_note.controllers.website_customer_note.request',
            fake_request,
        ):
            result = self.controller.save_customer_note(
                order_id='42',
                customer_note='  Customer note  ',
            )

        assert result == {'success': True}
        order.write.assert_called_once_with({'customer_note': 'Customer note'})

    def test_save_customer_note_returns_error_for_missing_order(self):
        order = MagicMock()
        order.exists.return_value = False
        fake_env = MagicMock()
        fake_env.__getitem__.return_value.sudo.return_value.browse.return_value = order
        fake_request = self._make_request()
        fake_request.env = fake_env

        with patch(
            'odoo.addons.website_customer_note.controllers.website_customer_note.request',
            fake_request,
        ):
            result = self.controller.save_customer_note(order_id='999', customer_note='Note')

        assert result == {'success': False, 'error': 'Order not found'}
        order.write.assert_not_called()
