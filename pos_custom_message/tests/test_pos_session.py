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
class TestPosSession(TransactionCase):
    """Test cases for the pos_session model."""

    def setUp(self):
        super(TestPosSession, self).setUp()
        # Create a POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config',
        })

    def test_pos_session_load_data_models(self):
        """Test _load_pos_data_models of pos.session."""
        models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn('pos.custom.message', models,
                      "pos.custom.message should be in loaded models")
