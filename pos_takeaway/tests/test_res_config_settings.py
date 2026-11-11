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
class TestResConfigSettings(TransactionCase):
    """Test cases for the res.config.settings takeaway related fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Settings Takeaway Test POS',
            'is_pos_takeaway': True,
            'is_generate_token': True,
            'pos_token': 7,
        })

    def test_settings_related_fields_read_pos_config_values(self):
        """Settings related fields should read values from the POS config."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })

        self.assertTrue(settings.pos_is_pos_takeaway)
        self.assertTrue(settings.pos_is_generate_token)
        self.assertEqual(settings.pos_pos_token, 7)

    def test_settings_related_fields_write_pos_config_values(self):
        """Settings related fields should write through to the POS config."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_is_pos_takeaway': False,
            'pos_is_generate_token': False,
        })

        self.pos_config.invalidate_recordset()
        self.assertFalse(self.pos_config.is_pos_takeaway)
        self.assertFalse(self.pos_config.is_generate_token)

        settings.write({
            'pos_is_pos_takeaway': True,
            'pos_is_generate_token': True,
        })

        self.pos_config.invalidate_recordset()
        self.assertTrue(self.pos_config.is_pos_takeaway)
        self.assertTrue(self.pos_config.is_generate_token)

    def test_settings_view_contains_takeaway_fields(self):
        """The POS settings view exposes the Take Away options."""
        view = self.env.ref('point_of_sale.res_config_settings_view_form')
        arch = self.env['res.config.settings'].get_view(
            view_id=view.id)['arch']

        self.assertIn('pos_is_pos_takeaway', arch)
        self.assertIn('pos_is_generate_token', arch)

    def test_settings_token_is_read_only(self):
        """The token counter cannot be changed from the settings."""
        field = self.env['res.config.settings']._fields['pos_pos_token']

        self.assertTrue(field.readonly)
        self.assertEqual(field.related, 'pos_config_id.pos_token')

    def test_settings_disable_takeaway_keeps_token(self):
        """Disabling Take Away keeps the last issued token number."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        settings.write({'pos_is_pos_takeaway': False})

        self.pos_config.invalidate_recordset()
        self.assertFalse(self.pos_config.is_pos_takeaway)
        self.assertEqual(self.pos_config.pos_token, 7)
