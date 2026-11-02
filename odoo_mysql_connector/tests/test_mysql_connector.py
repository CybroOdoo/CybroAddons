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
from unittest.mock import MagicMock, patch
import mysql.connector

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMysqlConnector(TransactionCase):
    """Unit test suite for MySQL Credential and Connector workflows."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initial records."""
        super().setUpClass()
        cls.credential = cls.env['mysql.credential'].create({
            'name': 'test_db',
            'user': 'test_user',
            'host': 'localhost',
            'password': 'secret_password',
        })
        cls.target_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner.category')], limit=1
        )
        cls.field_name = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.target_model.id), ('name', '=', 'name')], limit=1
        )
        cls.field_parent = cls.env['ir.model.fields'].search(
            [('model_id', '=', cls.target_model.id), ('name', '=', 'parent_id')], limit=1
        )
        cls.connector = cls.env['mysql.connector'].create({
            'name': 'Category Import',
            'credential_id': cls.credential.id,
            'sql_table': 'mysql_categories',
            'model_id': cls.target_model.id,
        })

    def test_credential_action_connect_success(self):
        """Test successful connection validation on mysql.credential."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        with patch('mysql.connector.connect', return_value=mock_conn) as mock_connect:
            self.credential.action_connect()
            mock_connect.assert_called_once_with(
                host=self.credential.host,
                user=self.credential.user,
                password=self.credential.password,
                database=self.credential.name
            )
            self.assertEqual(self.credential.state, 'connect')
            mock_conn.close.assert_called_once()

    def test_credential_action_connect_failure(self):
        """Test connection failure raises ValidationError with translated message."""
        with patch('mysql.connector.connect', side_effect=mysql.connector.Error("Access denied")):
            with self.assertRaises(ValidationError) as error_ctx:
                self.credential.action_connect()
            self.assertIn("Error connecting to MySQL", str(error_ctx.exception))
            self.assertEqual(self.credential.state, 'draft')

    def test_connector_onchange_model_id(self):
        """Test onchange resets synchronization mappings and fetched state."""
        self.connector.write({'is_fetched': True})
        self.env['sync.table'].create({
            'connection_id': self.connector.id,
            'mysql_field': 'category_name',
            'data_type': 'varchar',
            'ir_field_id': self.field_name.id,
        })
        self.assertTrue(self.connector.sync_ids)
        self.connector._onchange_model_id()
        self.assertFalse(self.connector.sync_ids)
        self.assertFalse(self.connector.is_fetched)

    def test_connector_fetch_data_success(self):
        """Test schema detection and foreign key mapping during action_fetch_data."""
        mock_columns = [
            {'Field': 'id', 'Type': 'int', 'Key': 'PRI'},
            {'Field': 'title', 'Type': 'varchar(255)', 'Key': ''},
            {'Field': 'parent_ref', 'Type': 'int', 'Key': ''},
        ]

        def fake_mysql_connect(query, params=None):
            if "SHOW COLUMNS" in query:
                return mock_columns
            if "INFORMATION_SCHEMA.KEY_COLUMN_USAGE" in query:
                if params and len(params) >= 3 and params[2] == 'parent_ref':
                    return [{
                        'CONSTRAINT_NAME': 'fk_parent',
                        'COLUMN_NAME': 'parent_ref',
                        'REFERENCED_TABLE_NAME': 'mysql_parent_table',
                        'REFERENCED_COLUMN_NAME': 'id'
                    }]
                return []
            return []

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            self.connector.action_fetch_data()
            self.assertEqual(self.connector.state, 'fetched')
            self.assertEqual(len(self.connector.sync_ids), 3)

            parent_sync = self.connector.sync_ids.filtered(lambda s: s.mysql_field == 'parent_ref')
            self.assertTrue(parent_sync.foreign_key)
            self.assertEqual(parent_sync.ref_table, 'mysql_parent_table')
            self.assertEqual(parent_sync.ref_col, 'id')

    def test_connector_fetch_data_no_pk_error(self):
        """Test action_fetch_data raises error when MySQL table lacks Primary/Unique key."""
        mock_columns = [
            {'Field': 'title', 'Type': 'varchar(255)', 'Key': ''},
            {'Field': 'description', 'Type': 'text', 'Key': ''},
        ]
        with patch.object(type(self.connector), 'mysql_connect', return_value=mock_columns):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.action_fetch_data()
            self.assertIn("does not have a Unique or Primary key", str(error_ctx.exception))

    def test_connector_sync_table_success(self):
        """Test successful record synchronization into Odoo model and audit logs."""
        self.env['sync.table'].create({
            'connection_id': self.connector.id,
            'mysql_field': 'category_title',
            'data_type': 'varchar',
            'ir_field_id': self.field_name.id,
            'foreign_key': False,
        })
        mock_columns = [
            {'Field': 'id', 'Type': 'int', 'Key': 'PRI'},
            {'Field': 'category_title', 'Type': 'varchar(255)', 'Key': ''},
        ]
        mock_records = [
            {'id': 501, 'category_title': 'Enterprise Solutions'},
            {'id': 502, 'category_title': 'Cloud Services'},
        ]

        def fake_mysql_connect(query):
            if "SHOW COLUMNS" in query:
                return mock_columns
            if "SELECT *" in query:
                return mock_records
            return []

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            self.connector.action_sync_table()
            self.assertEqual(self.connector.state, 'sync')

            created_tags = self.env['res.partner.category'].search([
                ('name', 'in', ['Enterprise Solutions', 'Cloud Services'])
            ])
            self.assertEqual(len(created_tags), 2)

            imported_entries = self.env['imported.data'].search([
                ('mysql_table', '=', 'mysql_categories'),
                ('mysql_ref', 'in', ['501', '502'])
            ])
            self.assertEqual(len(imported_entries), 2)
            self.assertEqual(set(imported_entries.mapped('log_note')), {'Success'})

    def test_connector_sync_table_missing_required_field_error(self):
        """Test action_sync_table raises error when target model required field is omitted."""
        # 'name' is required on res.partner.category, but we leave sync_ids empty
        mock_columns = [{'Field': 'id', 'Type': 'int', 'Key': 'PRI'}]
        with patch.object(type(self.connector), 'mysql_connect', return_value=mock_columns):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.action_sync_table()
            self.assertIn("Must provide values for the Odoo fields", str(error_ctx.exception))

    def test_connector_sync_table_no_pk_error(self):
        """Test action_sync_table raises error when table has no Primary/Unique key."""
        self.env['sync.table'].create({
            'connection_id': self.connector.id,
            'mysql_field': 'title',
            'data_type': 'varchar',
            'ir_field_id': self.field_name.id,
        })
        mock_columns = [{'Field': 'title', 'Type': 'varchar', 'Key': ''}]
        mock_records = [{'title': 'Sample'}]

        def fake_mysql_connect(query):
            if "SHOW COLUMNS" in query:
                return mock_columns
            return mock_records

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.action_sync_table()
            self.assertIn("does not have a Unique or Primary key", str(error_ctx.exception))

    def test_connector_sync_table_foreign_key_flow(self):
        """Test foreign key dependency resolution and missing parent validation."""
        # 1. Map parent_id with foreign_key=True
        self.env['sync.table'].create([
            {
                'connection_id': self.connector.id,
                'mysql_field': 'category_title',
                'data_type': 'varchar',
                'ir_field_id': self.field_name.id,
                'foreign_key': False,
            },
            {
                'connection_id': self.connector.id,
                'mysql_field': 'parent_ref',
                'data_type': 'int',
                'ir_field_id': self.field_parent.id,
                'foreign_key': True,
                'ref_table': 'mysql_parent_cat',
                'ref_col': 'id',
            }
        ])
        mock_columns = [
            {'Field': 'id', 'Type': 'int', 'Key': 'PRI'},
            {'Field': 'category_title', 'Type': 'varchar', 'Key': ''},
            {'Field': 'parent_ref', 'Type': 'int', 'Key': ''},
        ]
        mock_records = [
            {'id': 601, 'category_title': 'Child Category', 'parent_ref': 999}
        ]

        def fake_mysql_connect(query):
            if "SHOW COLUMNS" in query:
                return mock_columns
            return mock_records

        # Failure path: parent table not yet synchronized
        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.action_sync_table()
            self.assertIn("Please synchronize the mysql_parent_cat table first", str(error_ctx.exception))

        # Success path: create imported parent reference and resync
        parent_tag = self.env['res.partner.category'].create({'name': 'Parent Category'})
        self.env['imported.data'].create({
            'model_id': self.target_model.id,
            'mysql_table': 'mysql_parent_cat',
            'mysql_ref': '999',
            'odoo_ref': parent_tag.id,
            'log_note': 'Success',
        })

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            self.connector.action_sync_table()
            child_category = self.env['res.partner.category'].search([('name', '=', 'Child Category')], limit=1)
            self.assertTrue(child_category)
            self.assertEqual(child_category.parent_id.id, parent_tag.id)

    def test_connector_sync_table_datatype_conversion_error(self):
        """Test action_sync_table raises error on incompatible field datatypes."""
        self.env['sync.table'].create({
            'connection_id': self.connector.id,
            'mysql_field': 'due_date',
            'data_type': 'date',
            'ir_field_id': self.field_name.id,  # 'name' is char, date is not in ['char', 'selection']
            'foreign_key': False,
        })
        mock_columns = [
            {'Field': 'id', 'Type': 'int', 'Key': 'PRI'},
            {'Field': 'due_date', 'Type': 'date', 'Key': ''},
        ]
        mock_records = [{'id': 701, 'due_date': '2026-10-31'}]

        def fake_mysql_connect(query):
            if "SHOW COLUMNS" in query:
                return mock_columns
            return mock_records

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.action_sync_table()
            self.assertIn("cannot be converted to the data type", str(error_ctx.exception))

    def test_connector_mysql_connect_direct(self):
        """Test connector.mysql_connect execution and error handling."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'result': 1}]

        # Direct success
        with patch('mysql.connector.connect', return_value=mock_conn):
            res = self.connector.mysql_connect("SELECT 1;")
            self.assertEqual(res, [{'result': 1}])
            self.assertTrue(self.connector.is_fetched)
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()

        # Connection error
        with patch('mysql.connector.connect', side_effect=mysql.connector.Error("Connection timed out")):
            with self.assertRaises(ValidationError) as error_ctx:
                self.connector.mysql_connect("SELECT 1;")
            self.assertIn("Error connecting to MySQL", str(error_ctx.exception))

    def test_connector_invalid_table_identifier(self):
        """Test SQL injection attempt in table name is blocked by validator and constraint."""
        with self.assertRaises(ValidationError) as error_ctx:
            self.connector.write({'sql_table': 'users; DROP TABLE users;--'})
        self.assertIn("Invalid MySQL identifier", str(error_ctx.exception))

    def test_connector_sync_table_many2one_int_mapping_success(self):
        """Test non-FK integer-to-many2one mapping succeeds with lowercase many2one."""
        parent_tag = self.env['res.partner.category'].create({'name': 'Direct Category'})
        self.env['sync.table'].create([
            {
                'connection_id': self.connector.id,
                'mysql_field': 'category_title',
                'data_type': 'varchar',
                'ir_field_id': self.field_name.id,
                'foreign_key': False,
            },
            {
                'connection_id': self.connector.id,
                'mysql_field': 'parent_id',
                'data_type': 'int',
                'ir_field_id': self.field_parent.id,
                'foreign_key': False,
            }
        ])
        mock_columns = [
            {'Field': 'id', 'Type': 'int', 'Key': 'PRI'},
            {'Field': 'category_title', 'Type': 'varchar', 'Key': ''},
            {'Field': 'parent_id', 'Type': 'int', 'Key': ''},
        ]
        mock_records = [
            {'id': 801, 'category_title': 'Tagged Category', 'parent_id': parent_tag.id}
        ]

        def fake_mysql_connect(query, *args, **kwargs):
            if "SHOW COLUMNS" in query:
                return mock_columns
            if "SELECT *" in query:
                return mock_records
            return []

        with patch.object(type(self.connector), 'mysql_connect', side_effect=fake_mysql_connect):
            self.connector.action_sync_table()
            tagged_cat = self.env['res.partner.category'].search([('name', '=', 'Tagged Category')], limit=1)
            self.assertTrue(tagged_cat)
            self.assertEqual(tagged_cat.parent_id.id, parent_tag.id)

    def test_security_group_user_cannot_access_credentials(self):
        """Test regular internal users (base.group_user) cannot read or write mysql.credential."""
        internal_user = self.env['res.users'].create({
            'name': 'Regular Internal User',
            'login': 'reg_user_test',
            'email': 'reg_user@example.com',
            'group_ids': [fields.Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.credential.with_user(internal_user).read(['name', 'password'])

    def test_imported_data_views_and_action(self):
        """Test imported.data audit log action and default ordering."""
        log1 = self.env['imported.data'].create({
            'model_id': self.target_model.id,
            'mysql_table': 'mysql_test',
            'mysql_ref': '101',
            'odoo_ref': 1,
            'log_note': 'Success',
        })
        log2 = self.env['imported.data'].create({
            'model_id': self.target_model.id,
            'mysql_table': 'mysql_test',
            'mysql_ref': '102',
            'odoo_ref': 2,
            'log_note': 'Success',
        })
        logs = self.env['imported.data'].search([('mysql_table', '=', 'mysql_test')])
        self.assertEqual(logs[0].id, log2.id)
        action = self.env.ref('odoo_mysql_connector.imported_data_action')
        self.assertTrue(action)
        self.assertEqual(action.res_model, 'imported.data')
