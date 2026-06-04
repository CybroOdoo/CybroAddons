# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjitha V(odoo@cybrosys.com)
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

class TestSaleOrderCustomerNote(TransactionCase):
    """
    Tests for SaleOrderInherited (website_customer_note module).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal partner required for sale.order
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})

    def _make_order(self, note=None):
        """Create a minimal sale.order, optionally with a customer_note."""
        vals = {
            'partner_id': self.partner.id,
        }
        if note is not None:
            vals['customer_note'] = note
        return self.env['sale.order'].create(vals)

    # -----------------------------------------------------------------------
    # 1. Field definition
    # -----------------------------------------------------------------------

    def test_customer_note_field_exists(self):
        """customer_note must be a Text field defined on sale.order."""
        field = self.env['sale.order']._fields.get('customer_note')
        self.assertIsNotNone(field, "Field 'customer_note' must be defined on sale.order")
        self.assertEqual(field.type, 'text', "customer_note must be of type Text")

    def test_customer_note_label(self):
        """customer_note field string must be 'Customer Note'."""
        field = self.env['sale.order']._fields['customer_note']
        self.assertEqual(field.string, 'Customer Note')

    def test_customer_note_default_is_false(self):
        """customer_note must default to False/empty when not set."""
        order = self._make_order()
        self.assertFalse(
            order.customer_note,
            "customer_note must be False/empty when no note is provided at creation",
        )

    # -----------------------------------------------------------------------
    # 2. Direct field write / read-back
    # -----------------------------------------------------------------------

    def test_customer_note_set_at_creation(self):
        """A note provided during create() must be stored correctly."""
        order = self._make_order(note='Please deliver before noon.')
        self.assertEqual(order.customer_note, 'Please deliver before noon.')

    def test_customer_note_orm_write(self):
        """Writing customer_note via ORM write() must persist the value."""
        order = self._make_order()
        order.write({'customer_note': 'Handle with care.'})
        self.assertEqual(order.customer_note, 'Handle with care.')


    def test_customer_note_orm_clear(self):
        """Writing False/None to customer_note must clear it."""
        order = self._make_order(note='Some note.')
        order.write({'customer_note': False})
        self.assertFalse(order.customer_note)


    def test_customer_note_long_text(self):
        """customer_note must handle long text (>1000 chars)."""
        note = 'A' * 2000
        order = self._make_order(note=note)
        self.assertEqual(order.customer_note, note)

    # -----------------------------------------------------------------------
    # 3. write_customer_note() RPC method — success paths
    # -----------------------------------------------------------------------

    def test_write_customer_note_returns_true(self):
        """write_customer_note() must return True on success."""
        order = self._make_order()
        result = self.env['sale.order'].write_customer_note(order.id, 'Test note.')
        self.assertTrue(result, "write_customer_note() must return True on success")

    def test_write_customer_note_persists_value(self):
        """Note written via write_customer_note() must be readable from the order."""
        order = self._make_order()
        self.env['sale.order'].write_customer_note(order.id, 'Shipped separately.')
        order.invalidate_recordset()
        self.assertEqual(order.customer_note, 'Shipped separately.')

    def test_write_customer_note_empty_string(self):
        """write_customer_note() with empty string must store empty string."""
        order = self._make_order(note='Existing note.')
        result = self.env['sale.order'].write_customer_note(order.id, '')
        self.assertTrue(result)
        order.invalidate_recordset()
        self.assertFalse(
            order.customer_note,
            "An empty string note should result in a falsy customer_note",
        )

    def test_write_customer_note_overwrites_existing(self):
        """Calling write_customer_note() twice must store only the latest value."""
        order = self._make_order(note='Old note.')
        self.env['sale.order'].write_customer_note(order.id, 'New note.')
        order.invalidate_recordset()
        self.assertEqual(order.customer_note, 'New note.')

    def test_write_customer_note_long_text(self):
        """write_customer_note() must handle long text without truncation."""
        order = self._make_order()
        note = 'B' * 3000
        self.env['sale.order'].write_customer_note(order.id, note)
        order.invalidate_recordset()
        self.assertEqual(order.customer_note, note)

    # -----------------------------------------------------------------------
    # 4. write_customer_note() — invalid / edge inputs
    # -----------------------------------------------------------------------

    def test_write_customer_note_nonexistent_id_raises(self):
        """write_customer_note() with a non-existent ID must raise an error."""
        fake_id = 999999999
        with self.assertRaises(Exception):
            self.env['sale.order'].write_customer_note(fake_id, 'Ghost note.')

    def test_write_customer_note_none_note(self):
        """write_customer_note() with None must clear the field (falsy)."""
        order = self._make_order(note='Existing.')
        result = self.env['sale.order'].write_customer_note(order.id, None)
        self.assertTrue(result)
        order.invalidate_recordset()
        self.assertFalse(order.customer_note)

    # -----------------------------------------------------------------------
    # 5. Batch / multiple sequential calls
    # -----------------------------------------------------------------------

    def test_write_customer_note_multiple_calls_same_order(self):
        """Multiple sequential write_customer_note() calls must each update the field."""
        order = self._make_order()
        notes = ['First', 'Second', 'Third']
        for note in notes:
            self.env['sale.order'].write_customer_note(order.id, note)
        order.invalidate_recordset()
        self.assertEqual(order.customer_note, 'Third')

    def test_customer_note_independent_on_multiple_orders(self):
        """Each order must independently hold its own customer_note."""
        orders_and_notes = [
            (self._make_order(), 'Note A'),
            (self._make_order(), 'Note B'),
            (self._make_order(), 'Note C'),
        ]
        for order, note in orders_and_notes:
            self.env['sale.order'].write_customer_note(order.id, note)
        for order, note in orders_and_notes:
            order.invalidate_recordset()
            self.assertEqual(order.customer_note, note)
