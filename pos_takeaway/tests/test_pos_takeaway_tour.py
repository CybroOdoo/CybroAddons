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

from odoo.addons.pos_restaurant.tests.test_frontend import TestFrontendCommon


@tagged('post_install', '-at_install')
class TestPosTakeAwayTour(TestFrontendCommon):
    """Runs the Take Away flow in the POS as a cashier."""

    def test_pos_takeaway_tour(self):
        """Take Away and Dine-In orders get the right flag, token and
        receipt."""
        # No kitchen printer, so paying does not ask to send the order.
        self.pos_config.write({
            'is_pos_takeaway': True,
            'is_generate_token': True,
            'is_order_printer': False,
        })
        self.pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour('PosTakeAwayTour')
        orders = self.env['pos.order'].search(
            [('session_id', '=', self.pos_config.current_session_id.id)],
            order='id')
        self.assertEqual(len(orders), 2)
        takeaway, dine_in = orders
        self.assertTrue(takeaway.is_takeaway)
        self.assertEqual(takeaway.takeaway_token, 1)
        self.assertFalse(dine_in.is_takeaway)
        self.assertEqual(dine_in.takeaway_token, 0)
        self.assertEqual(self.pos_config.pos_token, 1)

    def test_pos_takeaway_button_hidden_when_disabled(self):
        """Without the setting, the button is not in the POS."""
        self.pos_config.write({'is_pos_takeaway': False})
        self.pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour('PosTakeAwayHiddenTour')
