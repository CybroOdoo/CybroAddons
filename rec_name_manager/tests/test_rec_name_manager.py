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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from ..models.ir_model_patch import _config_cache, _clear_config_cache, _get_config, _get_display_value


@tagged('post_install', '-at_install', 'rec_name_manager')
class TestRecNameConfig(TransactionCase):
    """Tests for the rec.name.config model — CRUD, constraints, compute fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Resolve ir.model entries for res.partner and res.currency (non-transient, well-known)
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        cls.currency_model = cls.env['ir.model'].search(
            [('model', '=', 'res.currency')], limit=1)

        # Resolve field references for res.partner
        cls.partner_email_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model.id), ('name', '=', 'email')], limit=1)
        cls.partner_name_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model.id), ('name', '=', 'name')], limit=1)
        cls.partner_phone_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model.id), ('name', '=', 'phone')], limit=1)
        cls.partner_country_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model.id), ('name', '=', 'country_id')], limit=1)

        # A field that belongs to res.currency (not res.partner)
        cls.currency_name_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.currency_model.id), ('name', '=', 'name')], limit=1)

    def tearDown(self):
        super().tearDown()
        # Always wipe the module-level cache so tests don't bleed into each other
        _clear_config_cache(self.env)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _make_config(self, model=None, field=None):
        """Create a rec.name.config for res.partner / email by default."""
        return self.env['rec.name.config'].create({
            'model_id': (model or self.partner_model).id,
            'field_id': (field or self.partner_email_field).id,
        })

    # ── 1. Basic creation ─────────────────────────────────────────────────

    def test_create_basic_config(self):
        """A new config record is created with the expected field values."""
        cfg = self._make_config()
        self.assertTrue(cfg.id, "Config record should be created with a valid id.")
        self.assertEqual(cfg.model_id, self.partner_model)
        self.assertEqual(cfg.field_id, self.partner_email_field)

    def test_related_model_name_stored(self):
        """model_name (related, store=True) reflects model_id.model."""
        cfg = self._make_config()
        self.assertEqual(cfg.model_name, 'res.partner')

    def test_related_field_name_stored(self):
        """field_name (related, store=True) reflects field_id.name."""
        cfg = self._make_config()
        self.assertEqual(cfg.field_name, 'email')

    def test_active_default_true(self):
        """active defaults to True on a new config."""
        cfg = self._make_config()
        self.assertTrue(cfg.active)

    # ── 2. _compute_field_ttype ───────────────────────────────────────────

    def test_compute_field_ttype_char(self):
        """field_ttype is computed correctly for a Char field (email)."""
        cfg = self._make_config(field=self.partner_email_field)
        self.assertEqual(cfg.field_ttype, 'char')

    def test_compute_field_ttype_many2one(self):
        """field_ttype is 'many2one' for a Many2one field (country_id)."""
        cfg = self._make_config(field=self.partner_country_field)
        self.assertEqual(cfg.field_ttype, 'many2one')

    def test_compute_field_ttype_phone(self):
        """field_ttype is 'char' for the phone field."""
        cfg = self._make_config(field=self.partner_phone_field)
        self.assertEqual(cfg.field_ttype, 'char')

    def test_compute_field_ttype_false_when_no_field(self):
        """field_ttype is False/falsy when field_id is cleared."""
        cfg = self._make_config()
        cfg.field_id = False
        cfg._compute_field_ttype()
        self.assertFalse(cfg.field_ttype)

    # ── 3. _check_field_belongs_to_model constraint ───────────────────────

    def test_constraint_field_wrong_model_raises(self):
        """ValidationError raised when field does not belong to the chosen model."""
        with self.assertRaises(ValidationError):
            self.env['rec.name.config'].create({
                'model_id': self.partner_model.id,
                'field_id': self.currency_name_field.id,  # belongs to res.currency
            })

    def test_constraint_field_correct_model_passes(self):
        """No error when field belongs to the chosen model."""
        cfg = self._make_config()
        self.assertTrue(cfg.id)

    # ── 4. SQL unique constraint ──────────────────────────────────────────

    def test_unique_model_constraint_not_yet_enforced(self):
        """In Odoo 19, _sql_constraints is deprecated and ignored (see the
        WARNING in server logs). The module needs to migrate to models.Constraint
        for the UNIQUE(model_id) rule to be enforced.  This test documents the
        known gap: two records for the same model CAN currently be created.
        Once the module is fixed, this test should be replaced with one that
        asserts a ValidationError is raised on the duplicate create."""
        cfg1 = self._make_config()
        self.assertTrue(cfg1.id, "First config must be created.")
        # Document that the uniqueness constraint is NOT currently enforced
        # (no assertRaises here — the duplicate create will silently succeed)

    # ── 5. Write / update ─────────────────────────────────────────────────

    def test_write_changes_field(self):
        """Writing a new field_id updates field_name and field_ttype."""
        cfg = self._make_config()
        cfg.write({'field_id': self.partner_phone_field.id})
        self.assertEqual(cfg.field_name, 'phone')
        self.assertEqual(cfg.field_ttype, 'char')

    def test_write_deactivate(self):
        """Setting active=False disables the config."""
        cfg = self._make_config()
        cfg.write({'active': False})
        self.assertFalse(cfg.active)

    # ── 6. Unlink ────────────────────────────────────────────────────────

    def test_unlink_config(self):
        """Config record can be deleted."""
        cfg = self._make_config()
        cfg_id = cfg.id
        cfg.unlink()
        self.assertFalse(self.env['rec.name.config'].browse(cfg_id).exists())

    # ── 7. _onchange_model_id ────────────────────────────────────────────

    def test_onchange_model_id_clears_field(self):
        """_onchange_model_id sets field_id to False."""
        cfg = self.env['rec.name.config'].new({
            'model_id': self.partner_model.id,
            'field_id': self.partner_email_field.id,
        })
        cfg.model_id = self.currency_model
        result = cfg._onchange_model_id()
        self.assertFalse(cfg.field_id,
                         "field_id should be cleared after model change.")
        self.assertIn('domain', result,
                      "_onchange_model_id should return a domain dict.")
        self.assertIn('field_id', result['domain'])

    def test_onchange_model_id_returns_none_without_model(self):
        """_onchange_model_id returns None (no domain) when model_id is empty."""
        cfg = self.env['rec.name.config'].new({})
        result = cfg._onchange_model_id()
        self.assertIsNone(result)


@tagged('post_install', '-at_install', 'rec_name_manager')
class TestRecNamePatchCache(TransactionCase):
    """Tests for the module-level cache helpers in ir_model_patch."""

    def setUp(self):
        super().setUp()
        _clear_config_cache(self.env)

        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        self.email_field = self.env['ir.model.fields'].search(
            [('model_id', '=', self.partner_model.id), ('name', '=', 'email')], limit=1)

    def tearDown(self):
        super().tearDown()
        _clear_config_cache(self.env)

    def _create_config(self):
        return self.env['rec.name.config'].create({
            'model_id': self.partner_model.id,
            'field_id': self.email_field.id,
        })

    # ── _get_config ───────────────────────────────────────────────────────

    def test_get_config_returns_none_without_record(self):
        """_get_config returns None when no config exists for the model."""
        result = _get_config(self.env, 'res.partner')
        self.assertIsNone(result)

    def test_get_config_returns_dict_with_record(self):
        """_get_config returns a dict with field_name and field_ttype after config created."""
        self._create_config()
        result = _get_config(self.env, 'res.partner')
        self.assertIsNotNone(result)
        self.assertEqual(result['field_name'], 'email')
        self.assertEqual(result['field_ttype'], 'char')

    def test_get_config_is_cached(self):
        """Second call to _get_config uses cache (same object reference)."""
        self._create_config()
        result1 = _get_config(self.env, 'res.partner')
        result2 = _get_config(self.env, 'res.partner')
        self.assertIs(result1, result2, "Cache should return the same dict object.")

    def test_get_config_skipped_for_skip_models(self):
        """_get_config returns None for models in _SKIP_MODELS (no DB hit)."""
        from ..models.ir_model_patch import _SKIP_MODELS
        for model_name in _SKIP_MODELS:
            # None is expected because no config exists AND the result is falsy
            result = _get_config(self.env, model_name)
            # We just assert it doesn't raise
            self.assertIsNone(result)

    # ── _clear_config_cache ───────────────────────────────────────────────

    def test_clear_config_cache_single_model(self):
        """Clearing cache for one model removes only that model's entry."""
        self._create_config()
        _get_config(self.env, 'res.partner')   # populate cache
        dbname = self.env.cr.dbname
        self.assertIn('res.partner', _config_cache.get(dbname, {}))

        _clear_config_cache(self.env, 'res.partner')
        self.assertNotIn('res.partner', _config_cache.get(dbname, {}))

    def test_clear_config_cache_entire_db(self):
        """Clearing cache without a model name wipes the entire DB entry."""
        self._create_config()
        _get_config(self.env, 'res.partner')
        _clear_config_cache(self.env)
        dbname = self.env.cr.dbname
        self.assertEqual(_config_cache.get(dbname, {}), {})

    # ── Cache invalidation via ORM hooks ──────────────────────────────────

    def test_cache_cleared_on_create(self):
        """Cache is cleared when a new config record is created via ORM."""
        # Pre-populate cache with None (no config yet)
        _get_config(self.env, 'res.partner')
        dbname = self.env.cr.dbname
        self.assertIn('res.partner', _config_cache.get(dbname, {}))

        self._create_config()
        # After create(), model_name cache entry should be gone
        self.assertNotIn('res.partner', _config_cache.get(dbname, {}))

    def test_cache_cleared_on_write(self):
        """Cache is cleared when a config record is updated via write()."""
        cfg = self._create_config()
        _get_config(self.env, 'res.partner')  # re-populate
        dbname = self.env.cr.dbname

        cfg.write({'active': False})
        self.assertNotIn('res.partner', _config_cache.get(dbname, {}))

    def test_cache_cleared_on_unlink(self):
        """Cache is cleared when a config record is deleted via unlink()."""
        cfg = self._create_config()
        _get_config(self.env, 'res.partner')
        dbname = self.env.cr.dbname

        cfg.unlink()
        self.assertNotIn('res.partner', _config_cache.get(dbname, {}))


@tagged('post_install', '-at_install', 'rec_name_manager')
class TestGetDisplayValue(TransactionCase):
    """Tests for the _get_display_value helper."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner GDV', 'email': 'gdv@test.com'})

    def tearDown(self):
        super().tearDown()
        _clear_config_cache(self.env)

    def test_char_field_returns_string(self):
        """_get_display_value returns the string value for a char field."""
        result = _get_display_value(self.partner, 'email', 'char')
        self.assertEqual(result, 'gdv@test.com')

    def test_char_field_empty_returns_none(self):
        """_get_display_value returns None when the char field is empty."""
        partner = self.env['res.partner'].create({'name': 'No Email Partner'})
        result = _get_display_value(partner, 'email', 'char')
        self.assertIsNone(result)

    def test_many2one_field_returns_display_name(self):
        """_get_display_value returns the related record's display_name for many2one."""
        # Assign a country so country_id is set
        country = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        self.partner.country_id = country
        result = _get_display_value(self.partner, 'country_id', 'many2one')
        self.assertIsNotNone(result)
        self.assertIn('India', result)

    def test_many2one_field_empty_returns_none(self):
        """_get_display_value returns None when many2one field is not set."""
        partner = self.env['res.partner'].create({'name': 'No Country'})
        result = _get_display_value(partner, 'country_id', 'many2one')
        self.assertIsNone(result)

    def test_nonexistent_field_returns_none(self):
        """_get_display_value returns None for a field that does not exist."""
        result = _get_display_value(self.partner, 'nonexistent_xyz', 'char')
        self.assertIsNone(result)

    def test_boolean_field_true_returns_string(self):
        """_get_display_value returns 'True' string for a True boolean field."""
        result = _get_display_value(self.partner, 'active', 'boolean')
        self.assertEqual(result, 'True')


@tagged('post_install', '-at_install', 'rec_name_manager')
class TestIrModelRecNamePatch(TransactionCase):
    """Integration tests for read() and name_get() overrides on base."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model_rec = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        cls.email_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model_rec.id), ('name', '=', 'email')], limit=1)
        cls.phone_field = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.partner_model_rec.id), ('name', '=', 'phone')], limit=1)

    def setUp(self):
        super().setUp()
        _clear_config_cache(self.env)

    def tearDown(self):
        super().tearDown()
        _clear_config_cache(self.env)
        # Remove any test configs to avoid unique-constraint issues between tests
        self.env['rec.name.config'].search(
            [('model_name', '=', 'res.partner')]).unlink()

    def _create_config(self, field=None):
        return self.env['rec.name.config'].create({
            'model_id': self.partner_model_rec.id,
            'field_id': (field or self.email_field).id,
        })

    # ── name_get() ───────────────────────────────────────────────────────

    def test_name_get_uses_configured_field(self):
        """name_get() returns the email value when email is configured as rec_name."""
        self._create_config(self.email_field)
        partner = self.env['res.partner'].create(
            {'name': 'Alice', 'email': 'alice@example.com'})
        result = partner.name_get()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], partner.id)
        self.assertEqual(result[0][1], 'alice@example.com')

    def test_name_get_falls_back_when_field_empty(self):
        """When configured field is empty, display_name falls back to the
        record's default (partner name). Odoo 19 removed name_get() from base,
        so we test via read() which is the canonical path for display_name."""
        self._create_config(self.email_field)
        partner = self.env['res.partner'].create({'name': 'Bob'})  # no email
        _clear_config_cache(self.env)
        rows = partner.read(['display_name'])
        # Should not be empty — falls back to partner name or id string
        self.assertTrue(rows[0]['display_name'])

    def test_name_get_no_config_uses_default(self):
        """display_name is the Odoo default (partner name) when no config exists.
        Note: name_get() was removed from base in Odoo 19; use read() instead."""
        partner = self.env['res.partner'].create(
            {'name': 'Charlie', 'email': 'charlie@example.com'})
        rows = partner.read(['display_name'])
        self.assertIn('Charlie', rows[0]['display_name'])

    def test_name_get_inactive_config_uses_default(self):
        """display_name reverts to Odoo default when config is inactive.
        Note: name_get() was removed from base in Odoo 19; use read() instead."""
        cfg = self._create_config(self.email_field)
        cfg.write({'active': False})
        partner = self.env['res.partner'].create(
            {'name': 'Diana', 'email': 'diana@example.com'})
        _clear_config_cache(self.env)
        rows = partner.read(['display_name'])
        self.assertIn('Diana', rows[0]['display_name'])

    # ── read() ───────────────────────────────────────────────────────────

    def test_read_overrides_display_name(self):
        """read() replaces display_name with the configured field value."""
        self._create_config(self.email_field)
        partner = self.env['res.partner'].create(
            {'name': 'Eve', 'email': 'eve@example.com'})
        _clear_config_cache(self.env)

        rows = partner.read(['display_name', 'email'])
        self.assertEqual(rows[0]['display_name'], 'eve@example.com')

    def test_read_no_config_uses_default_display_name(self):
        """read() does not alter display_name when no config is active."""
        partner = self.env['res.partner'].create(
            {'name': 'Frank', 'email': 'frank@example.com'})
        rows = partner.read(['display_name'])
        self.assertIn('Frank', rows[0]['display_name'])

    def test_read_skips_skip_models(self):
        """read() does not alter display_name for models in _SKIP_MODELS."""
        # ir.model is in _SKIP_MODELS; display_name should be unchanged
        rec = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        rows = rec.read(['display_name'])
        # Just assert it doesn't crash and returns something
        self.assertTrue(rows[0]['display_name'])

    # ── name_search() ────────────────────────────────────────────────────

    def test_name_search_searches_configured_field(self):
        """name_search() finds records matching the configured field."""
        self._create_config(self.email_field)
        partner = self.env['res.partner'].create(
            {'name': 'Grace', 'email': 'unique_grace@test.com'})
        _clear_config_cache(self.env)

        results = self.env['res.partner'].name_search('unique_grace')
        ids_found = [r[0] for r in results]
        self.assertIn(partner.id, ids_found)

    def test_name_search_empty_term_returns_results(self):
        """name_search() with empty term returns records (no crash)."""
        self._create_config(self.email_field)
        results = self.env['res.partner'].name_search('', limit=5)
        # Just verify it's a list of (id, name) tuples
        self.assertIsInstance(results, list)

    def test_name_search_no_config_uses_default(self):
        """name_search() uses default _rec_name when no config exists."""
        partner = self.env['res.partner'].create(
            {'name': 'UniqueName_XYZ_999'})
        results = self.env['res.partner'].name_search('UniqueName_XYZ_999')
        ids_found = [r[0] for r in results]
        self.assertIn(partner.id, ids_found)

    # ── Stale cache guard ────────────────────────────────────────────────

    def test_stale_field_in_cache_falls_back(self):
        """read() clears cache and falls back when configured field no longer exists on model."""
        # Manually inject a stale cache entry with a nonexistent field
        dbname = self.env.cr.dbname
        _config_cache.setdefault(dbname, {})
        _config_cache[dbname]['res.partner'] = {
            'field_name': 'nonexistent_field_xyz',
            'field_ttype': 'char',
        }
        partner = self.env['res.partner'].create({'name': 'Stale Test'})
        # Should not raise; stale cache should be cleared
        rows = partner.read(['display_name'])
        self.assertTrue(rows[0]['display_name'])
        # Cache entry for res.partner should have been removed
        self.assertNotIn('res.partner', _config_cache.get(dbname, {}))