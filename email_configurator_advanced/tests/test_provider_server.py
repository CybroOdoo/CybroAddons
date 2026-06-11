# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Safa K B (odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProviderServer(TransactionCase):
    """Test cases for the ProviderServer model (models/provider_server.py).
    Covers: _onchange_smtp_encryption, _onchange_server_type.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['provider.server'].create({
            'name': 'Test Provider',
            'smtp_host': 'smtp.testprovider.com',
            'smtp_encryption': 'none',
            'smtp_port': 25,
            'server': 'imap.testprovider.com',
            'server_type': 'imap',
            'port': 143,
        })

    def test_onchange_smtp_encryption_ssl_sets_port_465(self):
        """Test _onchange_smtp_encryption() sets smtp_port to 465 when
        smtp_encryption is set to 'ssl'."""
        self.provider.smtp_encryption = 'ssl'
        self.provider._onchange_smtp_encryption()
        self.assertEqual(
            self.provider.smtp_port, 465,
            "smtp_port must be 465 when encryption is 'ssl'.")

    def test_onchange_smtp_encryption_none_sets_port_25(self):
        """Test _onchange_smtp_encryption() sets smtp_port to 25 when
        smtp_encryption is 'none'."""
        self.provider.smtp_encryption = 'none'
        self.provider._onchange_smtp_encryption()
        self.assertEqual(
            self.provider.smtp_port, 25,
            "smtp_port must be 25 when encryption is 'none'.")

    def test_onchange_smtp_encryption_starttls_sets_port_25(self):
        """Test _onchange_smtp_encryption() sets smtp_port to 25 when
        smtp_encryption is 'starttls' (not ssl)."""
        self.provider.smtp_encryption = 'starttls'
        self.provider._onchange_smtp_encryption()
        self.assertEqual(
            self.provider.smtp_port, 25,
            "smtp_port must be 25 when encryption is 'starttls'.")

    def test_onchange_smtp_encryption_switching_ssl_to_none_resets_port(self):
        """Test _onchange_smtp_encryption() correctly resets smtp_port from
        465 back to 25 when switching from 'ssl' to 'none'."""
        self.provider.smtp_encryption = 'ssl'
        self.provider._onchange_smtp_encryption()
        self.assertEqual(self.provider.smtp_port, 465)
        # Now switch back to none
        self.provider.smtp_encryption = 'none'
        self.provider._onchange_smtp_encryption()
        self.assertEqual(
            self.provider.smtp_port, 25,
            "smtp_port must reset to 25 when switching from 'ssl' to 'none'.")

    def test_onchange_server_type_pop_without_ssl_sets_port_110(self):
        """Test _onchange_server_type() sets port to 110 for 'pop' type
        without SSL."""
        self.provider.server_type = 'pop'
        self.provider.is_ssl = False
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 110,
            "Port must be 110 for POP server without SSL.")

    def test_onchange_server_type_pop_with_ssl_sets_port_995(self):
        """Test _onchange_server_type() sets port to 995 for 'pop' type
        with SSL enabled."""
        self.provider.server_type = 'pop'
        self.provider.is_ssl = True
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 995,
            "Port must be 995 for POP server with SSL.")

    def test_onchange_server_type_imap_without_ssl_sets_port_143(self):
        """Test _onchange_server_type() sets port to 143 for 'imap' type
        without SSL."""
        self.provider.server_type = 'imap'
        self.provider.is_ssl = False
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 143,
            "Port must be 143 for IMAP server without SSL.")

    def test_onchange_server_type_imap_with_ssl_sets_port_993(self):
        """Test _onchange_server_type() sets port to 993 for 'imap' type
        with SSL enabled."""
        self.provider.server_type = 'imap'
        self.provider.is_ssl = True
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 993,
            "Port must be 993 for IMAP server with SSL.")

    def test_onchange_server_type_local_resets_port_to_zero(self):
        """Test _onchange_server_type() resets port to 0 for 'local' server
        type regardless of SSL."""
        self.provider.server_type = 'local'
        self.provider.is_ssl = False
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 0,
            "Port must be 0 for 'local' server type.")

    def test_onchange_server_type_resets_port_before_computing(self):
        """Test _onchange_server_type() always resets port to 0 first,
        ensuring stale values are cleared before new calculation."""
        self.provider.port = 9999
        self.provider.server_type = 'local'
        self.provider.is_ssl = False
        self.provider._onchange_server_type()
        self.assertEqual(
            self.provider.port, 0,
            "Port must be reset to 0 for unknown/local server types.")