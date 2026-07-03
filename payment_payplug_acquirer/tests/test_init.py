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

import logging
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.addons.payment_payplug_acquirer import post_init_hook, uninstall_hook

_logger = logging.getLogger(__name__)


class TestInitHooks(TransactionCase):
    """
    Test suite for module hooks in __init__.py.
    """

    @patch('odoo.addons.payment_payplug_acquirer.setup_provider')
    def test_post_init_hook(self, mock_setup_provider):
        """Test if setup_provider is called correctly."""
        post_init_hook(self.env)
        mock_setup_provider.assert_called_once_with(self.env, 'payplug')

    @patch('odoo.addons.payment_payplug_acquirer.reset_payment_provider')
    def test_uninstall_hook(self, mock_reset_payment_provider):
        """Test if reset_payment_provider is called correctly."""
        uninstall_hook(self.env)
        mock_reset_payment_provider.assert_called_once_with(self.env, 'payplug')
