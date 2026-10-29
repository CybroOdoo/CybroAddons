# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestAdvancedChatterTour(HttpCase):
    """Test suite exercising advanced chatter UI toggles via web tour."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('base.user_admin').write({
            'login': 'admin',
            'password': 'admin',
        })

    def test_advanced_chatter_toggles_tour(self):
        """Execute web tour to test Message, Note, and Activity toggles."""
        partner = self.env['res.partner'].create({
            'name': 'Test Chatter Customer',
            'email': 'customer@test.example.com',
        })
        self.start_tour(
            f"/odoo/res.partner/{partner.id}",
            "advanced_chatter_view_tour",
            login="admin",
            timeout=60,
        )
