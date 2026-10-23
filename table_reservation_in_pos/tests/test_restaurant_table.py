# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged

from .common import TableReservationCommon


@tagged('post_install', '-at_install', 'table_reservation_in_pos')
class TestRestaurantTable(TableReservationCommon):

    # ---- field defaults ---------------------------------------------------
    def test_new_table_is_not_reserved_by_default(self):
        self.assertFalse(self.table_1.reserved)
        self.assertFalse(self.table_1.reservation_details)

    def test_fields_are_defined_with_expected_types(self):
        table_fields = self.Table._fields
        self.assertEqual(table_fields['reserved'].type, 'boolean')
        self.assertEqual(table_fields['reservation_details'].type, 'text')

    def test_create_table_already_reserved(self):
        table = self._make_table(reserved=True, reservation_details='VIP')
        self.assertTrue(table.reserved)
        self.assertEqual(table.reservation_details, 'VIP')

    # ---- reserve / unreserve (same writes as the POS frontend) -------------
    def test_reserve_sets_flag_and_details(self):
        self.table_1.write({
            'reserved': True,
            'reservation_details': 'John, 4 persons, 8 PM',
        })
        self.assertTrue(self.table_1.reserved)
        self.assertEqual(self.table_1.reservation_details,
                         'John, 4 persons, 8 PM')

    def test_reserve_persists_to_database(self):
        self.table_1.write({'reserved': True, 'reservation_details': 'Kept'})
        self.table_1.invalidate_recordset()
        self.assertTrue(self.table_1.reserved)
        self.assertEqual(self.table_1.reservation_details, 'Kept')

    def test_reserve_does_not_touch_other_tables(self):
        self.table_1.write({'reserved': True, 'reservation_details': 'Only me'})
        self.assertFalse(self.table_2.reserved)
        self.assertFalse(self.table_2.reservation_details)

    def test_reserve_keeps_unicode_and_multiline_text(self):
        details = 'Jos\u00e9 \u2013 6 pax\nWindow seat \u2605'
        self.table_1.write({'reserved': True, 'reservation_details': details})
        self.assertEqual(self.table_1.reservation_details, details)

    def test_unreserve_clears_flag_and_details(self):
        self.table_1.write({'reserved': True, 'reservation_details': 'Temp'})
        self.table_1.write({'reserved': False, 'reservation_details': ''})
        self.assertFalse(self.table_1.reserved)
        self.assertFalse(self.table_1.reservation_details)

    def test_unreserve_does_not_touch_other_tables(self):
        (self.table_1 | self.table_2).write(
            {'reserved': True, 'reservation_details': 'Group'})
        self.table_1.write({'reserved': False, 'reservation_details': ''})
        self.assertTrue(self.table_2.reserved)
        self.assertEqual(self.table_2.reservation_details, 'Group')

    def test_reserve_unreserve_reserve_cycle(self):
        self.table_3.write({'reserved': True, 'reservation_details': 'One'})
        self.table_3.write({'reserved': False, 'reservation_details': ''})
        self.table_3.write({'reserved': True, 'reservation_details': 'Two'})
        self.assertTrue(self.table_3.reserved)
        self.assertEqual(self.table_3.reservation_details, 'Two')

    # ---- POS data loading -------------------------------------------------
    def test_load_pos_data_fields_includes_reservation_fields(self):
        pos_fields = self.Table._load_pos_data_fields(self.config.id)
        self.assertIn('reserved', pos_fields)
        self.assertIn('reservation_details', pos_fields)

    def test_load_pos_data_fields_keeps_core_fields(self):
        pos_fields = self.Table._load_pos_data_fields(self.config.id)
        core = [f for f in pos_fields
                if f not in ('reserved', 'reservation_details')]
        self.assertTrue(core, 'Fields from the base module must be preserved')

    def test_load_pos_data_fields_no_duplicates_for_new_fields(self):
        pos_fields = self.Table._load_pos_data_fields(self.config.id)
        self.assertEqual(pos_fields.count('reserved'), 1)
        self.assertEqual(pos_fields.count('reservation_details'), 1)

    def test_reservation_fields_are_readable_by_pos_loader(self):
        """The fields advertised to the POS must be real, readable fields."""
        self.table_1.write({'reserved': True,
                            'reservation_details': 'Loader check'})
        readable = [f for f in self.Table._load_pos_data_fields(self.config.id)
                    if f in self.Table._fields]
        data = self.table_1.read(readable)[0]
        self.assertTrue(data['reserved'])
        self.assertEqual(data['reservation_details'], 'Loader check')
