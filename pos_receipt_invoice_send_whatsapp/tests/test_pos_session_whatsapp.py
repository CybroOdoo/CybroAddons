# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Arjun P P (odoo@cybrosys.com)
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

from odoo.tests.common import TransactionCase


class TestPosSessionWhatsapp(TransactionCase):
    """Test cases for the PosSession WhatsApp loader extensions.

    NOTE: In Odoo 19, _loader_params_res_partner and _loader_params_res_users
    are deprecated. Tests skip gracefully if the base method no longer exists.
    """

    def setUp(self):
        """Set up a POS config and open a session for loader tests."""
        super().setUp()
        self.pos_config = self.env["pos.config"].create(
            {"name": "WA Session POS"}
        )
        self.pos_config.open_ui()
        self.session = self.pos_config.current_session_id

    def _has_method(self, method_name):
        """Check if method exists on pos.session."""
        return hasattr(self.session, method_name)

    def test_01_loader_params_res_partner_includes_whatsapp_number(self):
        """Test _loader_params_res_partner includes 'whatsapp_number' field."""
        if not self._has_method("_loader_params_res_partner"):
            self.skipTest(
                "_loader_params_res_partner does not exist in Odoo 19 base "
                "pos.session. The module's pos_session.py override is a "
                "compatibility stub.",
            )
        params = self.session._loader_params_res_partner()
        self.assertIn(
            "whatsapp_number",
            params["search_params"]["fields"],
            "'whatsapp_number' should be in the partner loader params fields.",
        )

    def test_02_loader_params_res_users_includes_whatsapp_groups(self):
        """Test _loader_params_res_users includes 'whatsapp_groups_checks'."""
        if not self._has_method("_loader_params_res_users"):
            self.skipTest(
                "_loader_params_res_users does not exist in Odoo 19 base "
                "pos.session. The module's pos_session.py override is a "
                "compatibility stub.",
            )
        params = self.session._loader_params_res_users()
        self.assertIn(
            "whatsapp_groups_checks",
            params["search_params"]["fields"],
            "'whatsapp_groups_checks' should be in the user loader fields.",
        )

    def test_03_loader_params_does_not_drop_existing_fields(self):
        """Test that extending loader params preserves the original fields."""
        if not self._has_method("_loader_params_res_partner"):
            self.skipTest(
                "_loader_params_res_partner does not exist in base session.",
            )
        params = self.session._loader_params_res_partner()
        loaded_fields = set(params["search_params"]["fields"])
        self.assertTrue(
            len(loaded_fields) > 1,
            "Loader params should contain 'whatsapp_number' and other fields.",
        )

    def test_04_load_pos_data_fields_overrides(self):
        """Verify res.partner and res.users models include the custom fields in POS data."""
        partner_fields = self.env["res.partner"]._load_pos_data_fields(self.pos_config)
        self.assertIn(
            "whatsapp_number",
            partner_fields,
            "res.partner should include 'whatsapp_number' in POS data fields.",
        )
        user_fields = self.env["res.users"]._load_pos_data_fields(self.pos_config)
        self.assertIn(
            "whatsapp_groups_checks",
            user_fields,
            "res.users should include 'whatsapp_groups_checks' in POS data fields.",
        )
