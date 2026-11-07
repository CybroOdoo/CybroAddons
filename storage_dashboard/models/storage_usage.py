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
import os
import platform

import psutil

from odoo import api, models
from odoo.exceptions import AccessError
from odoo.tools import SQL, config

# Number of models shown on the chart, the largest first
CHART_MODEL_LIMIT = 20
MB = 1024 * 1024
GB = 1024 * MB


class StorageUsage(models.Model):
    """Storage used by the models of the database, and the database, server
    and Odoo configuration information shown on the dashboard"""
    _name = 'storage.usage'
    _description = 'Storage Usage'

    def _format_limit(self, value, unit, factor=1):
        """Configuration limit with its unit, or Unlimited when not set"""
        if not value:
            return self.env._('Unlimited')
        size = round(value / factor, 2) if factor != 1 else value
        return f'{size} {unit}'

    def _check_dashboard_access(self):
        """The dashboard shows server information: administrators only"""
        if not self.env.is_system():
            raise AccessError(self.env._(
                'Only the administrators can open the storage dashboard.'))

    @api.model
    def get_data(self):
        """Models using the most storage (table, indexes and large values)
        in MB, the largest first, for the chart"""
        self._check_dashboard_access()
        tables = {}
        for name, model in self.env.registry.items():
            if not model._abstract and model._auto:
                tables.setdefault(model._table, name)
        self.env.cr.execute(SQL("""
            SELECT c.relname, pg_total_relation_size(c.oid)
              FROM pg_class c
              JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = current_schema()
               AND c.relkind = 'r'
               AND c.relname = ANY(%s)
          ORDER BY 2 DESC, 1
             LIMIT %s
        """, list(tables), CHART_MODEL_LIMIT))
        rows = self.env.cr.fetchall()
        return {
            'x_data': [tables[table] for table, _size in rows],
            'y_data': [round(size / MB, 2) for _table, size in rows],
        }

    @api.model
    def get_info(self):
        """Database, server and Odoo configuration information"""
        self._check_dashboard_access()
        cr = self.env.cr
        cr.execute(SQL("SELECT version(), pg_database_size(current_database())"))
        db_version, db_size = cr.fetchone()
        cr.execute(SQL("""
            SELECT count(*) FROM information_schema.tables
             WHERE table_schema = current_schema()
        """))
        db_tables = cr.fetchone()[0]
        memory = psutil.virtual_memory()
        ram_usage = psutil.Process(os.getpid()).memory_info().rss
        return {
            'db_name': cr.dbname,
            'db_version': db_version,
            'db_date': self.env['ir.config_parameter'].sudo().get_str(
                'database.create_date'),
            'db_size': f'{round(db_size / MB, 2)} MB',
            'db_tables': db_tables,
            'db_user': config['db_user'],
            'total_memory': f'{round(memory.total / GB, 2)} GB',
            'used_memory': f'{round(memory.used / GB, 2)} GB',
            'available_memory': f'{round(memory.available / GB, 2)} GB',
            'cpu_usage': f'{psutil.cpu_percent(interval=None)} %',
            'ram_usage': f'{round(ram_usage / MB, 2)} MB',
            'os': f'{platform.system()} {platform.release()}',
            'soft_limit': self._format_limit(config['limit_memory_soft'], 'GB', GB),
            'hard_limit': self._format_limit(config['limit_memory_hard'], 'GB', GB),
            'transient_age_limit': self._format_limit(
                config['transient_age_limit'], self.env._('hours')),
            'limit_time_cpu': self._format_limit(config['limit_time_cpu'], 's'),
            'limit_request': config['limit_request'] or self.env._('Unlimited'),
            'limit_time_real': self._format_limit(config['limit_time_real'], 's'),
            'http_port': config['http_port'],
        }
