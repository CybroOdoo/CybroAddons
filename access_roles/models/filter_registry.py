# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import logging
import xml.etree.ElementTree as ET
from odoo import api, Command, fields, models

_logger = logging.getLogger(__name__)


class FilterRegistry(models.Model):
    """Stores and manages filters from search views."""
    _name = 'filter.registry'
    _description = 'Filter Registry'

    name = fields.Char(string='Filter Name', required=True)
    domain = fields.Char(string='Domain')
    string = fields.Char(string='Display Name')
    active = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', string='Model', ondelete='cascade')
    view_ids = fields.Many2many('ir.ui.view', string='View')


    def _get_filter_elements_from_arch(self, arch):
        """Parse the XML arch and return a list of <filter> elements
           that do not have 'group_by' in their context attribute."""
        try:
            root = ET.fromstring(arch)
        except ET.ParseError:
            return []
        filter_elements = []
        for filter_el in root.iter("filter"):
            context = filter_el.get("context", "")
            if "group_by" in context:
                continue
            filter_elements.append(filter_el)
        return filter_elements

    def _extract_filter_attributes_from_el(self, filter_el):
        """Extract attributes from a filter element."""
        return {
            'name': filter_el.get('name') or '',
            'domain': filter_el.get('domain') or '',
            'string': filter_el.get('string') or '',
        }

    def get_all_filters(self):
        """Collect all filters defined in search views.

        Wrapped in a top-level try/except so that any lock timeout or
        unexpected DB error during server startup does NOT prevent Odoo
        from initializing. The registry will be populated on the next
        successful run (e.g. module upgrade or manual trigger).
        """
        try:
            return self._get_all_filters_internal()
        except Exception as e:
            _logger.warning(
                "access_roles: get_all_filters() skipped due to error "
                "(likely a DB lock timeout during startup): %s", e
            )
            return {}

    def _get_all_filters_internal(self):
        """Internal implementation of get_all_filters."""
        search_views = self.env['ir.ui.view'].search([('type', '=', 'search')])
        filter_model = {}
        for view in search_views:
            if not view.arch:
                continue
            model_name = view.model
            if model_name not in filter_model:
                filter_model[model_name] = {
                    'filters': [],
                    'view_ids': []
                }
            filter_elements = self._get_filter_elements_from_arch(view.arch)
            for filter_el in filter_elements:
                attributes = self._extract_filter_attributes_from_el(filter_el)
                if not attributes['name']:
                    continue
                filter_info = {
                    'name': attributes['name'],
                    'domain': attributes['domain'],
                    'string': attributes['string']
                }
                if filter_info not in filter_model[model_name]['filters']:
                    filter_model[model_name]['filters'].append(filter_info)
            if view.id not in filter_model[model_name]['view_ids']:
                filter_model[model_name]['view_ids'].append(view.id)
        for model_name, data in filter_model.items():
            if not model_name:
                continue
            model_record = self.env['ir.model'].search(
                [('model', '=', model_name)], limit=1)
            if not model_record:
                continue
            for filter_info in data['filters']:
                self._create_or_update_filter(
                    filter_info['name'],
                    model_record.id,
                    data['view_ids'],
                    filter_info['domain'],
                    filter_info['string']
                )
        return filter_model

    def _create_or_update_filter(self, name, model_id, view_ids, domain, string):
        """Create or update a filter registry record.

        Uses a savepoint so that a PostgreSQL lock timeout on one record
        only rolls back that single operation and does not abort the
        entire startup transaction.
        """
        display_name = string if string else name
        vals = {
            'name': display_name,
            'model_id': model_id,
            'view_ids': [Command.link(view) for view in view_ids],
            'domain': domain,
            'string': string
        }
        try:
            with self.env.cr.savepoint():
                existing_filter = self.search([
                    ('name', '=', name),
                    ('model_id', '=', model_id)
                ], limit=1)
                if existing_filter:
                    existing_filter.write(vals)
                else:
                    self.create(vals)
        except Exception as e:
            _logger.warning(
                "access_roles: Skipping filter '%s' (model_id=%s) due to error "
                "(savepoint rolled back safely): %s", name, model_id, e
            )
