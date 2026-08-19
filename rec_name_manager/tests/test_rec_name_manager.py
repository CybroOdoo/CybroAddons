# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRecNameManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_model = cls.env['ir.model']._get('res.partner')

        cls.name_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'name')
        ], limit=1)

        cls.email_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'email')
        ], limit=1)

    def _clear_partner_config(self):
        self.env['rec.name.config'].search([
            ('model_id', '=', self.partner_model.id)
        ]).unlink()

    # ---------------------------------------------------------
    # Configuration Creation
    # ---------------------------------------------------------

    def test_config_creation(self):
        self._clear_partner_config()

        config = self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
        })

        self.assertTrue(config)
        self.assertEqual(config.model_name, 'res.partner')
        self.assertEqual(config.field_name, 'name')

    # ---------------------------------------------------------
    # Computed Field Type
    # ---------------------------------------------------------

    def test_compute_field_ttype(self):
        self._clear_partner_config()

        config = self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.email_field.id,
        })

        self.assertEqual(
            config.field_ttype,
            self.email_field.ttype
        )

    # ---------------------------------------------------------
    # Active Flag
    # ---------------------------------------------------------

    def test_active_default(self):
        self._clear_partner_config()

        config = self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
        })

        self.assertTrue(config.active)

    # ---------------------------------------------------------
    # Constraint Validation
    # ---------------------------------------------------------

    def test_field_model_validation(self):
        self._clear_partner_config()

        product_field = self.env['ir.model.fields'].search([
            ('model', '=', 'product.template'),
            ('name', '=', 'name')
        ], limit=1)

        with self.assertRaises(ValidationError):
            self.env['rec.name.config'].create({
                'model_id': self.partner_model.id,
                'field_id': product_field.id,
            })

    # ---------------------------------------------------------
    # SQL Constraint
    # ---------------------------------------------------------

    def test_unique_model_constraint(self):
        self._clear_partner_config()

        self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
        })

        with self.assertRaises(Exception):
            self.env['rec.name.config'].create({
                'model_id': self.partner_model.id,
                'field_id': self.email_field.id,
            })

    # ---------------------------------------------------------
    # Onchange
    # ---------------------------------------------------------

    def test_onchange_model_id(self):
        config = self.env['rec.name.config'].new({
            'model_id': self.partner_model.id,
        })

        result = config._onchange_model_id()

        self.assertFalse(config.field_id)
        self.assertIn('domain', result)
        self.assertIn('field_id', result['domain'])

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def test_write_configuration(self):
        self._clear_partner_config()

        config = self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
        })

        config.write({
            'field_id': self.email_field.id,
        })

        self.assertEqual(
            config.field_id.id,
            self.email_field.id
        )

    # ---------------------------------------------------------
    # Unlink
    # ---------------------------------------------------------

    def test_unlink_configuration(self):
        self._clear_partner_config()

        config = self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
        })

        config.unlink()

        self.assertFalse(config.exists())