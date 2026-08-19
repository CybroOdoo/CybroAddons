# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosCustomMessage(TransactionCase):
    """Test cases for the pos_custom_message module."""

    def setUp(self):
        super(TestPosCustomMessage, self).setUp()
        # Create a POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config',
        })
        # Create a Custom Message
        self.custom_message = self.env['pos.custom.message'].create({
            'title': 'Test Message',
            'message_text': 'This is a test message',
            'message_type': 'info',
            'execution_time': 10.5,
            'pos_config_ids': [(4, self.pos_config.id)]
        })

    def test_pos_custom_message_load_data(self):
        """Test _load_pos_data_domain and _load_pos_data_fields of pos.custom.message."""
        domain = self.env['pos.custom.message']._load_pos_data_domain({}, self.pos_config)
        self.assertIn(('pos_config_ids', 'in', self.pos_config.id), domain,
                      "Domain should filter by pos_config_ids")

        fields = self.env['pos.custom.message']._load_pos_data_fields(self.pos_config)
        expected_fields = ['id', 'message_type', 'title', 'message_text', 'execution_time', 'pos_config_ids']
        for field in expected_fields:
            self.assertIn(field, fields, f"Field {field} should be in load fields")


