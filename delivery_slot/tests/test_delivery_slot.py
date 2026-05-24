# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Manasa T P (odoo@cybrosys.com)
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
from datetime import date, timedelta
from odoo.tests.common import TransactionCase


class TestDeliverySlot(TransactionCase):
    """Test cases for the delivery.slot model.

    setUp() creates fresh slot.time records for every test method.
    Because each method gets unique slot_id values, no two methods can
    ever collide on the (delivery_date, slot_id) unique SQL constraint,
    even if they happen to pick the same delivery_date.
    """

    def setUp(self):
        super().setUp()
        self.DeliverySlot = self.env['delivery.slot']
        self.SlotTime = self.env['slot.time']

        # Fresh records per test → unique slot_id every time
        self.slot_morning = self.SlotTime.create({
            'name': 'DS Morning 8-12',
            'time_from': '8',
            'time_to': '12',
        })
        self.slot_afternoon = self.SlotTime.create({
            'name': 'DS Afternoon 13-17',
            'time_from': '13',
            'time_to': '17',
        })
        self.d1 = date.today() + timedelta(days=10)
        self.d2 = date.today() + timedelta(days=11)

    # -------------------------------------------------------------------------
    # Creation
    # -------------------------------------------------------------------------

    def test_create_delivery_slot_defaults(self):
        """Default delivery_limit=100 and active=True."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        self.assertEqual(slot.delivery_limit, 100)
        self.assertTrue(slot.active)

    def test_create_delivery_slot_with_custom_limit(self):
        """Custom delivery_limit is stored correctly."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'delivery_limit': 50,
        })
        self.assertEqual(slot.delivery_limit, 50)

    def test_create_delivery_slot_inactive(self):
        """A slot can be created in inactive state."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'active': False,
        })
        self.assertFalse(slot.active)

    # -------------------------------------------------------------------------
    # SQL Constraint: unique(delivery_date, slot_id)
    # -------------------------------------------------------------------------

    def test_unique_date_slot_constraint(self):
        """Creating the same (date, slot) twice raises an integrity error."""
        self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        with self.assertRaises(Exception):
            # Must flush first so Odoo sends the INSERT to Postgres
            self.DeliverySlot.create({
                'delivery_date': self.d1,
                'slot_id': self.slot_morning.id,
            })
            self.env.flush_all()

    def test_same_date_different_slot_allowed(self):
        """Same date, different slot_id — both records are created fine."""
        s1 = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        s2 = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_afternoon.id,
        })
        self.assertNotEqual(s1.id, s2.id)

    def test_same_slot_different_date_allowed(self):
        """Same slot_id, different dates — both records are created fine."""
        s1 = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        s2 = self.DeliverySlot.create({
            'delivery_date': self.d2,
            'slot_id': self.slot_morning.id,
        })
        self.assertNotEqual(s1.id, s2.id)

    # -------------------------------------------------------------------------
    # Computed: total_delivery
    # -------------------------------------------------------------------------

    def test_total_delivery_zero_with_no_orders(self):
        """total_delivery is 0 when no sale orders are linked."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        self.assertEqual(slot.total_delivery, 0)

    # -------------------------------------------------------------------------
    # Computed: remaining_slots
    # -------------------------------------------------------------------------

    def test_remaining_slots_equals_limit_when_no_deliveries(self):
        """remaining_slots == delivery_limit when there are no orders."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'delivery_limit': 30,
        })
        self.assertEqual(slot.remaining_slots, 30)

    def test_remaining_slots_formula(self):
        """remaining_slots == delivery_limit - total_delivery at all times."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'delivery_limit': 10,
        })
        self.assertEqual(
            slot.remaining_slots,
            slot.delivery_limit - slot.total_delivery,
        )

    # -------------------------------------------------------------------------
    # _rec_name
    # -------------------------------------------------------------------------

    def test_display_name_contains_delivery_date(self):
        """display_name (rec_name=delivery_date) must include the date string."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        self.assertIn(str(self.d1), slot.display_name)

    # -------------------------------------------------------------------------
    # _get_pending_delivery_orders early-return branch
    # -------------------------------------------------------------------------

    def test_get_pending_delivery_orders_missing_date_or_slot(self):
        """Returns empty recordset when delivery_date or slot_id is absent."""
        empty = self.DeliverySlot.new({})
        self.assertFalse(empty._get_pending_delivery_orders())

    # -------------------------------------------------------------------------
    # active toggle
    # -------------------------------------------------------------------------

    def test_deactivate_delivery_slot(self):
        """A slot can be deactivated after creation."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
        })
        slot.write({'active': False})
        self.assertFalse(slot.active)

    def test_reactivate_delivery_slot(self):
        """An inactive slot can be reactivated."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'active': False,
        })
        slot.with_context(active_test=False).write({'active': True})
        self.assertTrue(slot.active)

    # -------------------------------------------------------------------------
    # Update delivery_limit
    # -------------------------------------------------------------------------

    def test_update_delivery_limit_recalculates_remaining(self):
        """Updating delivery_limit is immediately reflected in remaining_slots."""
        slot = self.DeliverySlot.create({
            'delivery_date': self.d1,
            'slot_id': self.slot_morning.id,
            'delivery_limit': 10,
        })
        slot.write({'delivery_limit': 25})
        self.assertEqual(slot.delivery_limit, 25)
        self.assertEqual(slot.remaining_slots, 25 - slot.total_delivery)

    # -------------------------------------------------------------------------
    # Model metadata
    # -------------------------------------------------------------------------

    def test_model_name(self):
        self.assertEqual(self.env['delivery.slot']._name, 'delivery.slot')

    def test_model_description(self):
        self.assertEqual(self.env['delivery.slot']._description, 'Delivery slot')