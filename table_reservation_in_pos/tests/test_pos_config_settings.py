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
class TestPosConfigSettings(TableReservationCommon):

    # ---- pos.config -------------------------------------------------------
    def test_pos_config_field_definition(self):
        field = self.env['pos.config']._fields['table_reservation']
        self.assertEqual(field.type, 'boolean')
        self.assertEqual(field.string, 'Table Reservation')

    def test_pos_config_table_reservation_default_false(self):
        defaults = self.env['pos.config'].default_get(['table_reservation'])
        self.assertFalse(defaults.get('table_reservation'))

    def test_pos_config_table_reservation_can_be_toggled(self):
        self.config.table_reservation = True
        self.config.invalidate_recordset()
        self.assertTrue(self.config.table_reservation)
        self.config.table_reservation = False
        self.assertFalse(self.config.table_reservation)

    # ---- res.config.settings ---------------------------------------------
    def test_settings_field_is_related_and_editable(self):
        field = self.env['res.config.settings']._fields['table_reservation']
        self.assertEqual(field.type, 'boolean')
        self.assertEqual(field.related, 'pos_config_id.table_reservation')
        self.assertFalse(field.readonly)

    def test_settings_reads_value_from_pos_config(self):
        self.config.table_reservation = True
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.config.id,
        })
        self.assertTrue(settings.table_reservation)
        # A fresh read after the config changed must show the new value.
        self.config.table_reservation = False
        settings.invalidate_recordset(['table_reservation'])
        self.assertFalse(settings.table_reservation)

    def test_settings_write_propagates_to_pos_config(self):
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.config.id,
            'table_reservation': True,
        })
        self.assertTrue(settings.table_reservation)
        self.assertTrue(self.config.table_reservation)
        settings.table_reservation = False
        self.assertFalse(self.config.table_reservation)

    def test_settings_field_has_no_config_parameter(self):
        """The value lives on pos.config, not in ir.config_parameter."""
        field = self.env['res.config.settings']._fields['table_reservation']
        self.assertFalse(getattr(field, 'config_parameter', None))

    # ---- POS data loading -------------------------------------------------
    def test_load_pos_data_fields_exposes_table_reservation(self):
        pos_fields = self.env['pos.config']._load_pos_data_fields(
            self.config.id)
        # An empty list means that every field is loaded.
        if pos_fields:
            self.assertIn('table_reservation', pos_fields)
            self.assertEqual(pos_fields.count('table_reservation'), 1)

    # ---- settings view ----------------------------------------------------
    def test_settings_view_is_active_and_inherits_pos_view(self):
        view = self.env.ref(
            'table_reservation_in_pos.res_config_settings_view_form')
        self.assertEqual(view.model, 'res.config.settings')
        self.assertEqual(
            view.inherit_id,
            self.env.ref('point_of_sale.res_config_settings_view_form'))

    def test_settings_form_contains_table_reservation_field(self):
        arch = self.env['res.config.settings'].get_view(
            view_type='form')['arch']
        self.assertIn('name="table_reservation"', arch)
