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
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger

CONFIG_MODULE = 'odoo.addons.rec_name_manager.models.rec_name_config'


@tagged('post_install', '-at_install', 'rec_name_manager')
class TestRecNameManager(TransactionCase):
    """Tests for the rec.name.config model and the display name override."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env['rec.name.config']
        cls.Partner = cls.env['res.partner']
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.currency_model = cls.env['ir.model']._get('res.currency')
        cls.country = cls.env.ref('base.be')
        cls.partner = cls.Partner.create({
            'name': 'Alice Rec',
            'email': 'alice.rec@example.com',
            'type': 'invoice',
            'color': 7,
            'country_id': cls.country.id,
        })
        cls.partner_no_email = cls.Partner.create({'name': 'Bob Rec'})

    def _field(self, model, name):
        """Return the ir.model.fields record of ``model.name``."""
        return self.env['ir.model.fields']._get(model, name)

    def _configure(self, field_name, model='res.partner'):
        """Create a configuration for ``model`` using ``field_name``."""
        return self.Config.create({
            'model_id': self.env['ir.model']._get(model).id,
            'field_id': self._field(model, field_name).id,
        })

    def _display_name(self, record):
        """Return the display name of ``record`` freshly computed."""
        record.invalidate_recordset(['display_name'])
        return record.display_name

    # ------------------------------------------------------------------
    # rec.name.config
    # ------------------------------------------------------------------
    def test_create_config_related_fields(self):
        """Related fields are filled from the selected model and field."""
        config = self._configure('email')
        self.assertEqual(config.model_name, 'res.partner')
        self.assertEqual(config.field_name, 'email')
        self.assertEqual(config.field_ttype, 'char')
        self.assertTrue(config.active)
        self.assertEqual(config.display_name, self.partner_model.name)

    def test_unique_model_constraint(self):
        """Only one configuration is allowed per model."""
        self._configure('email')
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), \
                self.env.cr.savepoint():
            self._configure('phone')

    def test_field_of_other_model_rejected(self):
        """A field of another model cannot be selected."""
        with self.assertRaises(ValidationError):
            self.Config.create({
                'model_id': self.partner_model.id,
                'field_id': self._field('res.currency', 'name').id,
            })

    def test_excluded_model_rejected(self):
        """The display name of the configuration models cannot change."""
        with self.assertRaises(ValidationError):
            self._configure('model', model='ir.model')

    def test_unsupported_field_type_rejected(self):
        """Fields of an unsupported type (one2many) are rejected."""
        with self.assertRaises(ValidationError):
            self._configure('child_ids')

    def test_onchange_model_clears_field(self):
        """Changing the model clears a field of the previous model."""
        form = Form(self.Config)
        form.model_id = self.partner_model
        form.field_id = self._field('res.partner', 'email')
        form.model_id = self.partner_model
        self.assertEqual(form.field_id, self._field('res.partner', 'email'))
        form.model_id = self.currency_model
        self.assertFalse(form.field_id)

    def test_cache_follows_create_write_unlink(self):
        """The cached configurations follow every change."""
        config = self._configure('email')
        self.assertEqual(self.Config._get_active_configs()['res.partner'],
                         ('email', 'char'))
        config.field_id = self._field('res.partner', 'phone')
        self.assertEqual(self.Config._get_active_configs()['res.partner'],
                         ('phone', 'char'))
        config.active = False
        self.assertNotIn('res.partner', self.Config._get_active_configs())
        config.active = True
        self.assertIn('res.partner', self.Config._get_active_configs())
        config.unlink()
        self.assertNotIn('res.partner', self.Config._get_active_configs())

    def test_no_table_returns_empty(self):
        """Without the table (install/uninstall) no configuration is used."""
        self._configure('email')
        self.env.transaction.invalidate_ormcache()
        with patch(f'{CONFIG_MODULE}.table_exists', return_value=False):
            self.assertEqual(self.Config._get_active_configs(), {})
        self.env.transaction.invalidate_ormcache()

    # ------------------------------------------------------------------
    # Display name
    # ------------------------------------------------------------------
    def test_default_display_name_without_config(self):
        """Without configuration the default display name is kept."""
        self.assertEqual(self._display_name(self.partner), 'Alice Rec')
        self.assertIsNone(self.partner._get_rec_name_config())

    def test_char_field_display_name(self):
        """A char field is used as the display name."""
        self._configure('email')
        self.assertEqual(self._display_name(self.partner),
                         'alice.rec@example.com')

    def test_empty_value_falls_back_to_default(self):
        """Records with an empty configured field keep their name."""
        self._configure('email')
        self.assertEqual(self._display_name(self.partner_no_email), 'Bob Rec')

    def test_selection_field_uses_label(self):
        """A selection field shows its label, not its technical value."""
        self._configure('type')
        self.assertEqual(self._display_name(self.partner), 'Invoice')

    def test_many2one_field_uses_related_name(self):
        """A many2one field shows the name of the related record."""
        self._configure('country_id')
        self.assertEqual(self._display_name(self.partner),
                         self.country.display_name)

    def test_integer_field_display_name(self):
        """A numeric field is converted to text."""
        self._configure('color')
        self.assertEqual(self._display_name(self.partner), '7')

    def test_display_name_in_web_read_of_many2one(self):
        """Many2one values sent to the web client use the configured name."""
        self._configure('email')
        child = self.Partner.create({
            'name': 'Child Rec', 'parent_id': self.partner.id})
        self.env.invalidate_all()
        data = child.web_read({'parent_id': {'fields': {'display_name': {}}}})
        self.assertEqual(data[0]['parent_id']['display_name'],
                         'alice.rec@example.com')

    def test_archived_config_is_ignored(self):
        """An archived configuration restores the default name."""
        config = self._configure('email')
        config.action_archive()
        self.assertEqual(self._display_name(self.partner), 'Alice Rec')

    def test_excluded_model_keeps_name(self):
        """Excluded models never use a configuration."""
        self.assertIsNone(self.Config._get_rec_name_config())

    def test_missing_field_is_ignored(self):
        """A configuration on a field that no longer exists is ignored."""
        with patch.object(type(self.Config), '_get_active_configs',
                          return_value={'res.partner': ('gone', 'char')}):
            self.assertIsNone(self.partner._get_rec_name_config())
            self.assertEqual(self._display_name(self.partner), 'Alice Rec')

    def test_write_refreshes_display_name(self):
        """Writing the configured field refreshes the display name."""
        self._configure('email')
        self.assertEqual(self._display_name(self.partner),
                         'alice.rec@example.com')
        self.partner.email = 'new.rec@example.com'
        self.assertEqual(self.partner.display_name, 'new.rec@example.com')
        self.partner.name = 'Alice Renamed'
        self.assertEqual(self.partner.display_name, 'new.rec@example.com')

    # ------------------------------------------------------------------
    # name_search
    # ------------------------------------------------------------------
    def _search_ids(self, name, **kwargs):
        """Return the ids found by name_search on partners."""
        return [rid for rid, _name in self.Partner.name_search(name, **kwargs)]

    def test_name_search_without_config(self):
        """Without configuration name_search keeps its default behavior."""
        self.assertEqual(self.Partner.name_search('Alice Rec'),
                         [(self.partner.id, 'Alice Rec')])

    def test_name_search_char_field(self):
        """name_search matches the configured field and the default name."""
        self._configure('email')
        result = self.Partner.name_search('alice.rec@')
        self.assertIn((self.partner.id, 'alice.rec@example.com'), result)
        self.assertIn(self.partner_no_email.id, self._search_ids('Bob Rec'))

    def test_name_search_respects_domain(self):
        """The extra domain still restricts the results."""
        self._configure('email')
        ids = self._search_ids('alice.rec@',
                               domain=[('id', '!=', self.partner.id)])
        self.assertNotIn(self.partner.id, ids)

    def test_name_search_many2one_field(self):
        """name_search matches the name of the configured many2one."""
        self._configure('country_id')
        self.assertIn(self.partner.id, self._search_ids(self.country.name))

    def test_name_search_fallbacks(self):
        """Empty terms, negative operators and non-text fields use the
        default name_search."""
        self._configure('email')
        self.assertIn(self.partner.id, self._search_ids(''))
        self.assertNotIn(self.partner.id,
                         self._search_ids('Alice Rec', operator='not ilike'))
        self.Config.search([]).field_id = self._field('res.partner', 'color')
        self.assertIn(self.partner.id, self._search_ids('Alice Rec'))

    def test_name_search_non_searchable_field(self):
        """A non searchable computed field falls back to the default."""
        self._configure('tz_offset')
        self.assertIn(self.partner.id, self._search_ids('Alice Rec'))
        self.assertNotIn(self.partner.id, self._search_ids('+0000'))
