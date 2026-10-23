# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3 ), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3 ) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3 ) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestPosScreenPanePosition(TransactionCase):
    """Test cases for the pos_screen_pane_position module.

    Covers:
    - Definition and attributes of the 'screen_view' field in pos.config.
    - Default value assignment on new pos.config creation ('left').
    - Explicit creation with 'left' and 'right' positions.
    - Writing/updating the screen view position.
    - Duplicating (copying) a pos.config record preserving the setting.
    - Required constraint on the 'screen_view' field.
    - Search and read operations for 'screen_view'.
    - POS data loading ensuring 'screen_view' is included for the frontend.
    - Inherited pos.config form view rendering.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info('Setting up TestPosScreenPanePosition class')
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Main POS Config',
        })

    def test_01_screen_view_field_attributes(self):
        """Test that the screen_view field is properly defined with expected attributes."""
        _logger.info('Running test_01_screen_view_field_attributes')
        field = self.env['pos.config']._fields.get('screen_view')
        self.assertIsNotNone(field, "Field 'screen_view' should exist on pos.config")
        self.assertEqual(field.type, 'selection', "Field 'screen_view' must be of type Selection")
        self.assertEqual(field.string, 'Screen View')
        self.assertTrue(field.required, "Field 'screen_view' must be required")
        self.assertEqual(
            field.default(self.env['pos.config']),
            'left',
            "Default value for 'screen_view' must be 'left'"
        )
        selection_dict = dict(field.selection)
        self.assertEqual(
            selection_dict,
            {'left': 'Left', 'right': 'Right'},
            "Selection options must be [('left', 'Left'), ('right', 'Right')]"
        )

    def test_02_default_screen_view_on_create(self):
        """Creating a pos.config without specifying screen_view should default to 'left'."""
        _logger.info('Running test_02_default_screen_view_on_create')
        config = self.env['pos.config'].create({'name': 'Test POS Config Default'})
        self.assertEqual(
            config.screen_view,
            'left',
            "Newly created POS config must default to 'left' screen view"
        )

    def test_03_create_with_screen_view_right(self):
        """Creating a pos.config with screen_view='right' should save correctly."""
        _logger.info('Running test_03_create_with_screen_view_right')
        config = self.env['pos.config'].create({
            'name': 'Test POS Config Right',
            'screen_view': 'right',
        })
        self.assertEqual(
            config.screen_view,
            'right',
            "POS config created with screen_view='right' should have 'right'"
        )

    def test_04_create_with_screen_view_left(self):
        """Creating a pos.config with screen_view='left' should save correctly."""
        _logger.info('Running test_04_create_with_screen_view_left')
        config = self.env['pos.config'].create({
            'name': 'Test POS Config Left',
            'screen_view': 'left',
        })
        self.assertEqual(
            config.screen_view,
            'left',
            "POS config created with screen_view='left' should have 'left'"
        )

    def test_05_update_screen_view(self):
        """Updating screen_view from 'left' to 'right' and vice versa."""
        _logger.info('Running test_05_update_screen_view')
        config = self.pos_config
        self.assertEqual(config.screen_view, 'left')

        config.write({'screen_view': 'right'})
        self.assertEqual(config.screen_view, 'right')

        config.write({'screen_view': 'left'})
        self.assertEqual(config.screen_view, 'left')

    def test_06_copy_pos_config_preserves_screen_view(self):
        """Copying a pos.config should preserve the screen_view value."""
        _logger.info('Running test_06_copy_pos_config_preserves_screen_view')
        config = self.env['pos.config'].create({
            'name': 'Original POS Config',
            'screen_view': 'right',
        })
        copied_config = config.copy({'name': 'Copied POS Config'})
        self.assertEqual(
            copied_config.screen_view,
            'right',
            "Duplicated POS config must retain the original screen_view value"
        )

    def test_07_required_constraint(self):
        """Writing False or None to screen_view should fail validation."""
        _logger.info('Running test_07_required_constraint')
        with self.assertRaises((ValidationError, IntegrityError, Exception)), mute_logger('odoo.sql_db', 'odoo.models'):
            with self.env.cr.savepoint():
                self.pos_config.write({'screen_view': False})

    def test_08_search_read_pos_config(self):
        """Testing read and search_read operations on pos.config for screen_view."""
        _logger.info('Running test_08_search_read_pos_config')
        read_res = self.pos_config.read(['name', 'screen_view'])
        self.assertTrue(read_res)
        self.assertIn('screen_view', read_res[0])
        self.assertEqual(read_res[0]['screen_view'], self.pos_config.screen_view)

        search_res = self.env['pos.config'].search_read(
            [('id', '=', self.pos_config.id)],
            ['name', 'screen_view']
        )
        self.assertTrue(search_res)
        self.assertEqual(search_res[0]['screen_view'], self.pos_config.screen_view)

    def test_09_pos_config_form_view(self):
        """Test that the pos.config form view inherits correctly and includes screen_view."""
        _logger.info('Running test_09_pos_config_form_view')
        view_arch = self.env['pos.config'].get_view(view_type='form')['arch']
        self.assertIn(
            'name="screen_view"',
            view_arch,
            "The pos.config form view must contain the 'screen_view' field"
        )
        self.assertIn(
            'id="screen_position"',
            view_arch,
            "The pos.config form view must contain the 'screen_position' setting"
        )

    def test_10_pos_data_loading(self):
        """Test that the POS data loading mechanism includes screen_view for the frontend."""
        _logger.info('Running test_10_pos_data_loading')
        loaded_data = self.env['pos.config']._load_pos_data_read(self.pos_config, self.pos_config)
        self.assertTrue(loaded_data, "Loaded POS data should not be empty")
        self.assertIn(
            'screen_view',
            loaded_data[0],
            "'screen_view' must be included in the POS loaded config data for the frontend"
        )
        self.assertEqual(loaded_data[0]['screen_view'], self.pos_config.screen_view)
