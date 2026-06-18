# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: K Sai Saran Varma (odoo@cybrosys.com)
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
################################################################################
import mysql.connector
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MysqlConnector(models.Model):
    """Model for connecting with Mysql"""
    _name = 'mysql.connector'
    _description = 'Mysql Connector'

    name = fields.Char(string='Name', help='Name of the record',
                       required=True)
    credential_id = fields.Many2one('mysql.credential',
                                    string='Connection', domain="[('state', '=', 'connect')]",
                                    help='Choose the My Sql connection',
                                    required=True)
    sql_table = fields.Char(string='Mysql Table Name',
                            help='Name of the table in Mysql database',
                            required=True)
    model_id = fields.Many2one('ir.model', string='Odoo Table Name',
                               help='Database table in Odoo to which you have'
                                    ' to map the data',
                               domain=lambda self: [(
                                   'access_ids', 'not in',
                                   self.env.user.groups_id.ids)],
                               required=True, ondelete="cascade")
    sync_ids = fields.One2many('sync.table',
                               'connection_id',
                               string='Field Mapping',
                               help='Select the fields to be mapped')
    is_fetched = fields.Boolean(string='Is Fetched',
                                help='True if once data fetched from mysql')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('fetched', 'Fetched'),
        ('sync', 'Synced')
    ], string='Status', readonly=True, copy=False, default='draft', help="State of the record")

    @api.onchange('model_id', 'sql_table')
    def _onchange_model_id(self):
        """Method for reloading the one2many field"""
        self.sync_ids = False
        self.is_fetched = False

    def action_sync_table(self):
        """Method for syncing tables from MySQL to Odoo"""
        field_list = self.mysql_connect(f"SHOW COLUMNS FROM {self.sql_table};")
        records = self.mysql_connect(f"SELECT * FROM {self.sql_table};")

        # Prepare required fields excluding UOMs (we set them programmatically)
        required_fields = []
        for field in self.env['ir.model.fields'].search(
                [('model', '=', self.model_id.model),
                 ('required', '=', True),
                 ('ttype', 'not in', ['one2many', 'many2many'])]).mapped('name'):
            if field not in ['uom_id', 'uom_po_id'] and not \
                    self.env[self.model_id.model].default_get([field]):
                required_fields.append(field)

        # Validate mapping completeness
        if not set(required_fields).issubset(self.sync_ids.ir_field_id.mapped('name')):
            missing_fields = set(required_fields) - set(self.sync_ids.ir_field_id.mapped('name'))
            raise ValidationError(
                "Must provide values for the Odoo fields {}".format(", ".join(missing_fields)))

        # Detect unique or primary key
        unique = next((rec['Field'] for rec in field_list if rec.get('Key', '').upper() == 'PRI'),
                      next((rec['Field'] for rec in field_list if rec.get('Key', '').upper() == 'UNI'), None))
        if not unique:
            raise ValidationError(
                f"The MySQL table {self.sql_table} cannot be imported because it doesn't have a Unique or Primary key.")

        mysql_to_odoo_type_mapping = {
            'tinyint': ['boolean'],
            'smallint': ['integer', 'many2one'],
            'mediumint': ['integer', 'many2one'],
            'int': ['integer', 'many2one'],
            'bigint': ['integer', 'many2one'],
            'float': ['float'],
            'double': ['float'],
            'decimal': ['float'],
            'numeric': ['float'],
            'char': ['char'],
            'varchar': ['char'],
            'text': ['text'],
            'mediumtext': ['text'],
            'longtext': ['text'],
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

        # Sync each record
        if records:
            for item in records:
                vals = {}

                # Check if already synced
                imported = self.env['imported.data'].sudo().search(
                    [('model_id', '=', self.model_id.id),
                     ('mysql_ref', '=', item[unique]),
                     ('mysql_table', '=', self.sql_table),
                     ('log_note', '=', 'Success')])
                if imported:
                    continue

                # Map fields
                for rec in self.sync_ids:
                    if rec.ir_field_id:
                        mysql_data_type = rec.data_type.lower().split('(')[0]

                        # Validate type
                        if not rec.foreign_key and rec.ir_field_id.ttype not in mysql_to_odoo_type_mapping.get(
                                mysql_data_type, []):
                            raise ValidationError(
                                f'Data type of {rec.mysql_field} cannot be converted to the type of {rec.ir_field_id.name}')

                        # Handle foreign keys
                        if rec.foreign_key:
                            foreign_record = self.env['imported.data'].sudo().search(
                                [('mysql_table', '=', rec.ref_table),
                                 ('mysql_ref', '=', item[rec.mysql_field])])

                            if not foreign_record:
                                raise ValidationError(
                                    f'The {rec.mysql_field} field references a foreign table {rec.ref_table}. '
                                    'Please sync that table first.')

                            if rec.ir_field_id.ttype == 'many2one':
                                vals[rec.ir_field_id.name] = foreign_record.odoo_ref
                            else:
                                foreign_obj = self.env[foreign_record.model_id.model].browse(foreign_record.odoo_ref)
                                name_field = self.env[foreign_record.model_id.model]._rec_name
                                vals[rec.ir_field_id.name] = getattr(foreign_obj, name_field, None)
                        else:
                            vals[rec.ir_field_id.name] = item[rec.mysql_field]


                # Assign UOM defaults for product models
                if self.model_id.model in ['product.product', 'product.template']:
                    uom_unit = self.env.ref('uom.product_uom_unit').id
                    vals.setdefault('uom_id', uom_unit)
                    vals.setdefault('uom_po_id', uom_unit)


                # Create the record and log import
                if vals:
                    new_record = self.env[self.model_id.model].create(vals)
                    self.env['imported.data'].sudo().create({
                        'model_id': self.model_id.id,
                        'mysql_ref': item[unique],
                        'mysql_table': self.sql_table,
                        'odoo_ref': new_record.id,
                        'log_note': 'Success',
                    })

        self.write({'state': 'sync'})

    def action_fetch_data(self):
        """Method for fetching the columns of Mysql table"""
        records = self.mysql_connect(f"SHOW COLUMNS FROM {self.sql_table};")
        if not any(key in rec.get('Key', '') for rec in records for
                   key in ['PRI', 'UNI']):
            raise ValidationError(
                "The MySQL table cannot be imported because it "
                "doesn't have a Unique or Primary key.")
        self.sync_ids.unlink()
        if records:
            for rec in records:
                constraints = self.mysql_connect(
                    f"SELECT CONSTRAINT_NAME, COLUMN_NAME,"
                    f" REFERENCED_TABLE_NAME, "
                    f"REFERENCED_COLUMN_NAME FROM "
                    f"INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                    f"WHERE TABLE_NAME = "
                    f"'{self.sql_table}' and COLUMN_NAME = "
                    f"'{rec['Field']}' and REFERENCED_TABLE_NAME != 'None' and "
                    f"REFERENCED_COLUMN_NAME != 'None'")
                vals = {
                    'connection_id': self.id,
                    'data_type': rec['Type'],
                    'mysql_field': rec['Field'],
                    'model_id': self.model_id.id,
                    'foreign_key': True if constraints else False
                }
                if constraints:
                    vals['ref_table'] = constraints[0]['REFERENCED_TABLE_NAME']
                    vals['ref_col'] = constraints[0]['REFERENCED_COLUMN_NAME']
                if rec['Field'] not in self.sync_ids.sudo(
                ).search([('connection_id',
                           '=', self.id)]).mapped('mysql_field'):
                    self.sudo().write({
                        'sync_ids': [
                            (0, 0, vals)]
                    })
            self.write({
                'state': 'fetched'
            })

    def mysql_connect(self, query):
        """Method for connecting with Mysql"""
        try:
            connection = mysql.connector.connect(
                host=self.credential_id.host,
                user=self.credential_id.user,
                password=self.credential_id.password,
                database=self.credential_id.name
            )
            if not connection.is_connected():
                raise ValidationError(f"Error connecting to MySQL")
            cursor = connection.cursor(dictionary=True)
            # Execute your MySQL query
            cursor.execute(query)
            # Fetch the results and store them in a variable
            results = cursor.fetchall()
            # Set the flag after successfully fetching the data
            self.is_fetched = True
            # Close cursor and connection
            cursor.close()
            connection.close()
            return results
        except mysql.connector.Error as e:
            # Handle any connection errors
            raise ValidationError(f"Error connecting to MySQL: {e}")
