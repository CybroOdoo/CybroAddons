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
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

_config_cache = {}

_SKIP_MODELS = frozenset({
    'rec.name.config',
    'ir.model',
    'ir.model.fields',
    'base',
})


def _get_config(env, model_name):
    """
    Returns {'field_name': ..., 'field_ttype': ...} for model_name,
    or None if no active config exists.
    Results are cached per-database so the DB is only hit ONCE per model.
    """
    dbname = env.cr.dbname
    if dbname not in _config_cache:
        _config_cache[dbname] = {}
    cache = _config_cache[dbname]

    if model_name in cache:
        return cache[model_name]

    try:
        config = env['rec.name.config'].sudo().search(
            [('model_name', '=', model_name), ('active', '=', True)],
            limit=1,
        )
        if config:
            entry = {
                'field_name': config.field_name,
                'field_ttype': config.field_ttype or 'char',
            }
            cache[model_name] = entry
        else:
            cache[model_name] = None
    except Exception as e:
        _logger.warning('rec_name_manager: _get_config error for model=%s: %s', model_name, e)
        cache[model_name] = None

    return cache[model_name]


def _clear_config_cache(env, model_name=None):
    """
    Clears the cache entry for one model, or the entire DB cache.
    Called on create / write / unlink of rec.name.config records.
    """
    dbname = env.cr.dbname
    if dbname in _config_cache:
        if model_name and model_name in _config_cache[dbname]:
            del _config_cache[dbname][model_name]
        else:
            _config_cache[dbname] = {}


def _get_display_value(record, field_name, field_ttype):
    """
    Reads `field_name` from `record` and returns a display string.
    Returns None if the value is falsy so callers can fall back to the default.
    """
    try:
        value = getattr(record, field_name, None)

        if value is None or value is False or value == '':
            return None

        if field_ttype == 'many2one':
            return value.sudo().display_name if value else None

        if field_ttype == 'selection':
            field_obj = record.fields_get([field_name]).get(field_name, {})
            selection_map = dict(field_obj.get('selection', []))
            return selection_map.get(value, str(value))

        if field_ttype in ('float', 'integer', 'monetary'):
            return str(value)

        return str(value)

    except Exception as e:
        _logger.warning('rec_name_manager: _get_display_value error field=%s model=%s: %s',
                        field_name, record._name, e)
        return None


class RecNameConfigCacheInvalidator(models.Model):
    """Clear cached configuration when records change."""
    _inherit = 'rec.name.config'

    def write(self, vals):
        """Clear the cache after updating configurations."""
        result = super().write(vals)
        for rec in self:
            _clear_config_cache(self.env, rec.model_name)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Clear the cache after creating configurations."""
        records = super().create(vals_list)
        for rec in records:
            _clear_config_cache(self.env, rec.model_name)
        return records

    def unlink(self):
        """Clear the cache before deleting configurations."""
        for rec in self:
            _clear_config_cache(self.env, rec.model_name)
        return super().unlink()


class IrModelRecNamePatch(models.AbstractModel):
    """Customize record display names based on configuration."""
    _inherit = 'base'

    def read(self, fields=None, load='_classic_read'):
        """Override display names using the configured field."""
        result = super().read(fields=fields, load=load)

        model_name = self._name
        if model_name in _SKIP_MODELS:
            return result

        if not result or 'display_name' not in result[0]:
            return result

        config = _get_config(self.env, model_name)
        if not config:
            return result

        field_name = config['field_name']
        field_ttype = config['field_ttype']

        if field_name not in self._fields:
            _logger.warning('rec_name_manager: read() field %r no longer exists on %r. '
                            'Stale cache cleared.', field_name, model_name)
            _clear_config_cache(self.env, model_name)
            return result

        records_by_id = {r.id: r for r in self}

        for row in result:
            record = records_by_id.get(row['id'])
            if not record:
                continue
            try:
                display = _get_display_value(record, field_name, field_ttype)
                if display:
                    row['display_name'] = display
            except Exception as e:
                _logger.warning('rec_name_manager: read() error on %s id=%s: %s',
                                model_name, row['id'], e)

        return result

    # ------------------------------------------------------------------
    # name_get() — kept for many2one drop-downs and older call sites
    # ------------------------------------------------------------------
    def name_get(self):
        """Return configured display names for records."""
        model_name = self._name
        if model_name in _SKIP_MODELS:
            return super().name_get()

        config = _get_config(self.env, model_name)
        if not config:
            return super().name_get()

        field_name = config['field_name']
        field_ttype = config['field_ttype']

        if field_name not in self._fields:
            _clear_config_cache(self.env, model_name)
            return super().name_get()

        result = []
        for record in self:
            try:
                display = _get_display_value(record, field_name, field_ttype)
                if display:
                    result.append((record.id, display))
                else:
                    default = super(IrModelRecNamePatch, record).name_get()
                    result.append(default[0] if default else (record.id, str(record.id)))
            except Exception as e:
                _logger.warning('rec_name_manager: name_get() error on %s id=%s: %s',
                                model_name, record.id, e)
                default = super(IrModelRecNamePatch, record).name_get()
                result.append(default[0] if default else (record.id, str(record.id)))
        return result

    # ------------------------------------------------------------------
    # name_search() — controls what appears in many2one drop-down searches
    # ------------------------------------------------------------------
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Search records using the configured display field."""
        model_name = self._name
        if model_name in _SKIP_MODELS:
            return super().name_search(name, args, operator, limit)

        config = _get_config(self.env, model_name)
        if not config:
            return super().name_search(name, args, operator, limit)

        field_name = config['field_name']
        field_ttype = config['field_ttype']

        if field_name not in self._fields:
            _logger.warning('rec_name_manager: name_search() field %r missing on %r '
                            '— stale cache cleared.', field_name, model_name)
            _clear_config_cache(self.env, model_name)
            return super().name_search(name, args, operator, limit)

        args = args or []
        try:
            if name:
                if field_ttype == 'many2one':
                    domain = [(self._rec_name, operator, name)]
                else:
                    rec_name_field = self._rec_name or 'name'
                    if field_name != rec_name_field and rec_name_field in self._fields:
                        domain = ['|', (field_name, operator, name),
                                       (rec_name_field, operator, name)]
                    else:
                        domain = [(field_name, operator, name)]
            else:
                domain = []

            records = self.search(domain + args, limit=limit)
            return records.name_get()

        except Exception as e:
            _logger.warning('rec_name_manager: name_search error on %s: %s', model_name, e)
            return super().name_search(name, args, operator, limit)

    @api.model
    def _register_hook(self):
        """Register the model hook during initialization."""
        super()._register_hook()