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
class TestPosOrder(TransactionCase):
    """Test cases for the pos.order takeaway fields and views."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Order Take Away Test POS',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.user.id,
        })

    def _create_order(self, **values):
        order_values = {
            'session_id': self.pos_session.id,
            'config_id': self.pos_config.id,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
        }
        order_values.update(values)
        return self.env['pos.order'].create(order_values)

    def test_pos_order_takeaway_defaults(self):
        """POS orders are Dine-In (not Take Away) by default."""
        order = self._create_order()

        self.assertFalse(order.is_takeaway)
        self.assertEqual(order.takeaway_token, 0)

    def test_takeaway_token_generated_when_enabled(self):
        """Take Away orders get consecutive tokens stored on the order."""
        self.pos_config.is_generate_token = True
        first = self._create_order(is_takeaway=True)
        second = self._create_order(is_takeaway=True)
        dine_in = self._create_order()

        self.assertEqual(first.takeaway_token, 1)
        self.assertEqual(second.takeaway_token, 2)
        self.assertEqual(dine_in.takeaway_token, 0)
        self.assertEqual(self.pos_config.pos_token, 2)

    def test_takeaway_token_not_generated_when_disabled(self):
        """No token is issued when token generation is disabled."""
        self.pos_config.is_generate_token = False
        order = self._create_order(is_takeaway=True)

        self.assertTrue(order.is_takeaway)
        self.assertEqual(order.takeaway_token, 0)

    def test_toggle_back_to_dine_in_resets_token(self):
        """Switching a Take Away order back to Dine-In clears its token."""
        self.pos_config.is_generate_token = True
        order = self._create_order(is_takeaway=True)
        self.assertEqual(order.takeaway_token, 1)

        order.write({'is_takeaway': False})
        self.assertFalse(order.is_takeaway)
        self.assertEqual(order.takeaway_token, 0)

        order.write({'is_takeaway': True})
        self.assertEqual(order.takeaway_token, 2)

    def test_takeaway_search_filters_domains(self):
        """The Dine-In and Take Away filters return the matching orders."""
        takeaway = self._create_order(is_takeaway=True)
        dine_in = self._create_order()
        orders = takeaway | dine_in
        search_view = self.env.ref('pos_takeaway.view_pos_order_filter')

        self.assertIn('name="dine_in"', search_view.arch_db)
        self.assertIn('name="take_away"', search_view.arch_db)
        self.assertEqual(
            orders.filtered_domain([('is_takeaway', '=', True)]), takeaway)
        self.assertEqual(
            orders.filtered_domain([('is_takeaway', '=', False)]), dine_in)

    def test_takeaway_tokens_created_in_batch(self):
        """A batch create issues one unique token per Take Away order."""
        self.pos_config.is_generate_token = True
        values = {
            'session_id': self.pos_session.id,
            'config_id': self.pos_config.id,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
        }
        orders = self.env['pos.order'].create([
            dict(values, is_takeaway=True),
            dict(values),
            dict(values, is_takeaway=True),
        ])

        self.assertEqual(orders[0].takeaway_token, 1)
        self.assertEqual(orders[1].takeaway_token, 0)
        self.assertEqual(orders[2].takeaway_token, 2)

    def test_takeaway_token_is_not_reissued_on_rewrite(self):
        """Writing is_takeaway again keeps the token already issued."""
        self.pos_config.is_generate_token = True
        order = self._create_order(is_takeaway=True)

        order.write({'is_takeaway': True})
        # The order note field was renamed between Odoo versions, so use
        # whichever text field exists on pos.order in this database.
        note_field = next(
            (name for name in ('internal_note', 'general_note',
                               'general_customer_note', 'note')
             if name in order._fields), 'floating_order_name')
        order.write({note_field: 'Updated'})

        self.assertEqual(order.takeaway_token, 1)
        self.assertEqual(self.pos_config.pos_token, 1)

    def test_write_takeaway_on_existing_dine_in_order_issues_token(self):
        """Switching an existing Dine-In order to Take Away issues a token."""
        self.pos_config.is_generate_token = True
        order = self._create_order()
        self.assertEqual(order.takeaway_token, 0)

        order.write({'is_takeaway': True})

        self.assertEqual(order.takeaway_token, 1)

    def test_takeaway_token_not_copied(self):
        """Duplicating an order must not duplicate its token."""
        field = self.env['pos.order']._fields['takeaway_token']

        self.assertFalse(field.copy)

    def test_pos_data_fields_include_takeaway_fields(self):
        """Take Away fields are available in the POS frontend data."""
        fields_list = self.env['pos.order']._load_pos_data_fields(
            self.pos_config)

        # An empty list means that every field is loaded.
        if fields_list:
            self.assertIn('is_takeaway', fields_list)
            self.assertIn('takeaway_token', fields_list)

    def test_order_form_view_hides_table_for_takeaway(self):
        """Table and guests are hidden on the form for Take Away orders."""
        view = self.env.ref('pos_restaurant.view_pos_pos_form')
        arch = self.env['pos.order'].get_view(view_id=view.id)['arch']

        self.assertIn('is_takeaway', arch)
        self.assertIn('invisible="is_takeaway"', arch)
