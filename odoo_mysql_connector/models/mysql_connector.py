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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import re

import mysql.connector

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MysqlConnector(models.Model):
    """Model managing MySQL database connections, mapping, and data import."""
    _name = 'mysql.connector'
    _description = 'MySQL Connector'

    name = fields.Char(help='Name of the record', required=True)
    credential_id = fields.Many2one('mysql.credential',
                                    string='Connection', domain="[('state', '=', 'connect')]",
                                    help='Choose the MySQL connection',
                                    required=True)
    sql_table = fields.Char(string='MySQL Table Name',
                            help='Name of the table in MySQL database',
                            required=True)
    model_id = fields.Many2one('ir.model', string='Odoo Table Name',
                               help='Database table in Odoo to which you have to map the data',
                               domain="[('transient', '=', False), ('abstract', '=', False)]",
                               required=True, ondelete="cascade")
    sync_ids = fields.One2many('sync.table',
                               'connection_id',
                               string='Field Mapping',
                               help='Select the fields to be mapped')
    is_fetched = fields.Boolean(string='Is Fetched',
                                help='True if once data fetched from MySQL')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('fetched', 'Fetched'),
        ('sync', 'Synced')
    ], string='Status', readonly=True, copy=False, default='draft', help="State of the record")

    @api.constrains('sql_table')
    def _check_sql_table(self):
        """Validate MySQL table name identifier against SQL injection patterns."""
        for record in self:
            if record.sql_table:
                record._validate_sql_identifier(record.sql_table)

    def _validate_sql_identifier(self, identifier):
        """Validate and quote a MySQL identifier to prevent SQL injection."""
        clean_identifier = str(identifier or '').strip()
        if not clean_identifier or not re.match(r'^[A-Za-z0-9_]+$', clean_identifier):
            raise ValidationError(
                self.env._(
                    "Invalid MySQL identifier '%(name)s'. Only alphanumeric "
                    "characters and underscores are allowed.",
                    name=identifier
                )
            )
        return f"`{clean_identifier}`"

    @api.onchange('model_id', 'sql_table')
    def _onchange_model_id(self):
        """Method for reloading the one2many field upon model or table change."""
        self.sync_ids = False
        self.is_fetched = False

    def action_sync_table(self):
        """Synchronize MySQL table rows into the configured Odoo model."""
        self.ensure_one()
        quoted_table = self._validate_sql_identifier(self.sql_table)
        field_list = self.mysql_connect(f"SHOW COLUMNS FROM {quoted_table};")
        records = self.mysql_connect(f"SELECT * FROM {quoted_table};")
        required_fields = []
        for field in self.env['ir.model.fields'].search(
                [('model', '=', self.model_id.model),
                 ('required', '=', True),
                 ('ttype', 'not in',
                  ['one2many', 'many2many'])]).mapped('name'):
            if not self.env[self.model_id.model].default_get([field]):
                required_fields.append(field)
        if not set(required_fields).issubset(
                self.sync_ids.ir_field_id.mapped('name')):
            missing_fields = set(required_fields) - set(
                self.sync_ids.ir_field_id.mapped('name'))
            raise ValidationError(
                self.env._(
                    "Must provide values for the Odoo fields %(fields)s",
                    fields=", ".join(missing_fields)
                )
            )
        unique = next(
            (rec['Field'] for rec in field_list if
             rec.get('Key', '').upper() == 'PRI'),
            next((rec['Field'] for rec in field_list if
                  rec.get('Key', '').upper() == 'UNI'), None))
        if not unique:
            raise ValidationError(
                self.env._(
                    "The MySQL table %(table)s cannot be imported because it "
                    "does not have a Unique or Primary key.",
                    table=self.sql_table
                )
            )
        if records:
            mysql_to_odoo_type_mapping = {
                'tinyint': ['boolean', 'integer', 'selection'],
                'smallint': ['integer', 'many2one', 'selection'],
                'mediumint': ['integer', 'many2one', 'selection'],
                'int': ['integer', 'many2one', 'selection'],
                'bigint': ['integer', 'many2one', 'selection'],
                'float': ['float'],
                'double': ['float'],
                'decimal': ['float'],
                'numeric': ['float'],
                'char': ['char', 'selection'],
                'varchar': ['char', 'selection'],
                'enum': ['char', 'selection'],
                'text': ['text', 'selection'],
                'mediumtext': ['text', 'selection'],
                'longtext': ['text', 'selection'],
                'binary': ['binary'],
                'varbinary': ['binary'],
                'blob': ['binary'],
                'tinyblob': ['binary'],
                'mediumblob': ['binary'],
                'longblob': ['binary'],
                'date': ['date'],
                'datetime': ['datetime'],
                'timestamp': ['datetime'],
            }
            for item in records:
                vals = {}
                imported = self.env['imported.data'].sudo().search(
                    [('model_id', '=', self.model_id.id),
                     ('mysql_ref', '=', item[unique]),
                     ('mysql_table', '=', self.sql_table),
                     ('log_note', '=', 'Success')])
                if not imported:
                    for rec in self.sync_ids:
                        if rec.ir_field_id:
                            mysql_data_type = rec.data_type.lower().split('(')[0]
                            allowed_types = mysql_to_odoo_type_mapping.get(
                                mysql_data_type, ['char', 'text', 'selection'])
                            if not rec.foreign_key and rec.ir_field_id.ttype not in allowed_types:
                                raise ValidationError(
                                    self.env._(
                                        "Data type of %(mysql_field)s cannot be converted "
                                        "to the data type of %(odoo_field)s",
                                        mysql_field=rec.mysql_field,
                                        odoo_field=rec.ir_field_id.name
                                    )
                                )
                            if rec.foreign_key:
                                foreign_record = self.env[
                                    'imported.data'].sudo().search(
                                    [('mysql_table', '=', rec.ref_table),
                                     ('mysql_ref', '=', item[rec.mysql_field])])
                                if foreign_record:
                                    if rec.ir_field_id.ttype == 'many2one':
                                        vals[rec.ir_field_id.name] = foreign_record.odoo_ref
                                    else:
                                        foreign_record_browse = self.env[foreign_record.model_id.model].browse(
                                            foreign_record.odoo_ref)
                                        rec_name_field = self.env[foreign_record.model_id.model]._rec_name
                                        rec_name_value = getattr(foreign_record_browse, rec_name_field, None)
                                        if rec_name_value is not None:
                                            vals[rec.ir_field_id.name] = rec_name_value
                                else:
                                    raise ValidationError(
                                        self.env._(
                                            "The %(mysql_field)s column of %(main_table)s table establishes a "
                                            "foreign key relationship with the %(ref_table)s table in MySQL. "
                                            "Please synchronize the %(ref_table)s table first.",
                                            mysql_field=rec.mysql_field,
                                            main_table=self.sql_table,
                                            ref_table=rec.ref_table
                                        )
                                    )
                            else:
                                val = item[rec.mysql_field]
                                if rec.ir_field_id.ttype == 'selection' and val is not None:
                                    val_str = str(val).strip()
                                    field_obj = self.env[self.model_id.model]._fields.get(rec.ir_field_id.name)
                                    if field_obj and hasattr(field_obj, '_description_selection'):
                                        selection_options = field_obj._description_selection(self.env)
                                        key_map = {}
                                        for key, label in selection_options:
                                            key_map[str(key).lower()] = key
                                            key_map[str(label).lower()] = key
                                        val = key_map.get(val_str.lower(), val_str)
                                    else:
                                        val = val_str
                                vals[rec.ir_field_id.name] = val
                    if vals:
                        record = self.env[self.model_id.model].create(vals)
                        self.env['imported.data'].sudo().create({
                            'model_id': self.model_id.id,
                            'mysql_ref': item[unique],
                            'mysql_table': self.sql_table,
                            'odoo_ref': record.id,
                            'log_note': 'Success'
                        })
            self.write({
                'state': 'sync'
            })

    def action_fetch_data(self):
        """Fetch schema and column metadata from the configured MySQL table."""
        self.ensure_one()
        quoted_table = self._validate_sql_identifier(self.sql_table)
        records = self.mysql_connect(f"SHOW COLUMNS FROM {quoted_table};")
        if not any(key in rec.get('Key', '') for rec in records for
                   key in ['PRI', 'UNI']):
            raise ValidationError(
                self.env._(
                    "The MySQL table cannot be imported because it "
                    "does not have a Unique or Primary key."
                )
            )
        self.sync_ids.unlink()
        sync_vals = []
        if records:
            query = (
                "SELECT CONSTRAINT_NAME, COLUMN_NAME, "
                "REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                "FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = %s "
                "AND TABLE_NAME = %s "
                "AND COLUMN_NAME = %s "
                "AND REFERENCED_TABLE_NAME IS NOT NULL "
                "AND REFERENCED_COLUMN_NAME IS NOT NULL;"
            )
            for rec in records:
                col_name = rec['Field']
                self._validate_sql_identifier(col_name)
                constraints = self.mysql_connect(
                    query,
                    params=(self.credential_id.name, self.sql_table, col_name)
                )
                vals = {
                    'data_type': rec['Type'],
                    'mysql_field': col_name,
                    'model_id': self.model_id.id,
                    'foreign_key': bool(constraints)
                }
                if constraints:
                    vals['ref_table'] = constraints[0]['REFERENCED_TABLE_NAME']
                    vals['ref_col'] = constraints[0]['REFERENCED_COLUMN_NAME']
                sync_vals.append(fields.Command.create(vals))

            self.write({
                'sync_ids': sync_vals,
                'state': 'fetched'
            })

    def mysql_connect(self, query, params=None):
        """Execute a query on the connected MySQL database and return results."""
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=self.credential_id.host,
                user=self.credential_id.user,
                password=self.credential_id.password,
                database=self.credential_id.name
            )
            if not connection.is_connected():
                raise ValidationError(self.env._("Failed to establish connection to MySQL."))
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            self.is_fetched = True
            return results
        except mysql.connector.Error as e:
            raise ValidationError(
                self.env._("Error connecting to MySQL: %(error)s", error=e)
            )
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
