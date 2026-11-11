#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):
    """Test cases for the pos.config takeaway fields."""

    def test_pos_config_takeaway_fields_defaults(self):
        """Takeaway settings are disabled and token is empty by default."""
        pos_config = self.env['pos.config'].create({
            'name': 'Default Takeaway Test POS',
        })

        self.assertFalse(pos_config.is_pos_takeaway)
        self.assertFalse(pos_config.is_generate_token)
        self.assertEqual(pos_config.pos_token, 0)

    def test_pos_config_takeaway_fields_values(self):
        """The POS config stores takeaway and token settings."""
        pos_config = self.env['pos.config'].create({
            'name': 'Takeaway Test POS',
            'is_pos_takeaway': True,
            'is_generate_token': True,
            'pos_token': 5,
        })

        self.assertTrue(pos_config.is_pos_takeaway)
        self.assertTrue(pos_config.is_generate_token)
        self.assertEqual(pos_config.pos_token, 5)

    def test_next_takeaway_token_increments(self):
        """Each call returns the next token and persists it on the config."""
        pos_config = self.env['pos.config'].create({
            'name': 'Token Increment Test POS',
        })

        self.assertEqual(pos_config._get_next_takeaway_token(), 1)
        self.assertEqual(pos_config._get_next_takeaway_token(), 2)
        self.assertEqual(pos_config.pos_token, 2)
        pos_config.invalidate_recordset()
        self.assertEqual(pos_config.pos_token, 2)

    def test_next_takeaway_token_continues_from_existing_value(self):
        """The counter continues from the stored token number."""
        pos_config = self.env['pos.config'].create({
            'name': 'Token Continue Test POS',
            'pos_token': 9,
        })

        self.assertEqual(pos_config._get_next_takeaway_token(), 10)

    def test_takeaway_tokens_are_independent_per_pos(self):
        """Every POS keeps its own token counter."""
        config_a = self.env['pos.config'].create({'name': 'Token POS A'})
        config_b = self.env['pos.config'].create({'name': 'Token POS B'})

        config_a._get_next_takeaway_token()
        config_a._get_next_takeaway_token()

        self.assertEqual(config_b._get_next_takeaway_token(), 1)
        self.assertEqual(config_a.pos_token, 2)

    def test_pos_data_fields_include_takeaway_fields(self):
        """Take Away fields are available in the POS frontend data."""
        pos_config = self.env['pos.config'].create({
            'name': 'Load Fields Test POS',
        })
        fields_list = self.env['pos.config']._load_pos_data_fields(pos_config)

        # An empty list means that every field is loaded.
        if fields_list:
            for name in ('is_pos_takeaway', 'is_generate_token', 'pos_token'):
                self.assertIn(name, fields_list)
