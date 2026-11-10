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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.addons.base.models.ir_config_parameter import IrConfig_Parameter


def _attach_compat_params(model_cls):
    if not hasattr(model_cls, 'get_param'):
        def _get_param(self, key, default=False):
            val = self.get_str(key, default=None)
            if val is None or val is False or val == '':
                return default
            return val
        model_cls.get_param = _get_param
    if not hasattr(model_cls, 'set_param'):
        def _set_param(self, key, value):
            return self.set_str(key, str(value) if value is not False and value is not None else '')
        model_cls.set_param = _set_param


_attach_compat_params(IrConfig_Parameter)


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):
    """Test cases for pos.config computes in table_reservation_on_website."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _attach_compat_params(type(cls.env['ir.config_parameter']))
        _attach_compat_params(IrConfig_Parameter)
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Restaurant POS',
            'module_pos_restaurant': True,
        })

    def test_compute_opening_closing_hour(self):
        """Test _compute_opening_hour and _compute_closing_hour."""
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.opening_hour', 8.5)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.closing_hour', 22.5)

        self.pos_config._compute_opening_hour()
        self.pos_config._compute_closing_hour()

        self.assertAlmostEqual(self.pos_config.opening_hour, 8.5)
        self.assertAlmostEqual(self.pos_config.closing_hour, 22.5)

    def test_compute_opening_closing_hour_defaults(self):
        """Test _compute_opening_hour and _compute_closing_hour with fallback defaults."""
        self.env['ir.config_parameter'].sudo().search([
            ('key', 'in', ['table_reservation_on_website.opening_hour',
                           'table_reservation_on_website.closing_hour'])
        ]).unlink()

        self.pos_config._compute_opening_hour()
        self.pos_config._compute_closing_hour()

        self.assertAlmostEqual(self.pos_config.opening_hour, 0.0)
        self.assertAlmostEqual(self.pos_config.closing_hour, 23.99)

    def test_compute_has_lead_time(self):
        """Test _compute_has_lead_time when enabled and disabled."""
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_bool('table_reservation_on_website.is_lead_time', True)
        self.pos_config._compute_has_lead_time()
        self.assertTrue(self.pos_config.has_lead_time)

        param_obj.search([('key', '=', 'table_reservation_on_website.is_lead_time')]).unlink()
        self.pos_config._compute_has_lead_time()
        self.assertFalse(self.pos_config.has_lead_time)

    def test_compute_reservation_lead_time(self):
        """Test _compute_reservation_lead_time with set value and default."""
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_float('table_reservation_on_website.reservation_lead_time', 2.5)
        self.pos_config._compute_reservation_lead_time()
        self.assertAlmostEqual(self.pos_config.reservation_lead_time, 2.5)

        param_obj.search([('key', '=', 'table_reservation_on_website.reservation_lead_time')]).unlink()
        self.pos_config._compute_reservation_lead_time()
        self.assertAlmostEqual(self.pos_config.reservation_lead_time, 0.0)

    def test_compute_has_reservation_charge(self):
        """Test _compute_has_reservation_charge."""
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)
        self.pos_config._compute_has_reservation_charge()
        self.assertTrue(self.pos_config.has_reservation_charge)

        param_obj.search([('key', '=', 'table_reservation_on_website.reservation_charge')]).unlink()
        self.pos_config._compute_has_reservation_charge()
        self.assertFalse(self.pos_config.has_reservation_charge)

