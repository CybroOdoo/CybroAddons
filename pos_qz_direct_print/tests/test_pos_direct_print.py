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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch
import base64

class TestPosDirectPrint(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPosDirectPrint, cls).setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config',
            'system_printer_name': 'Test_Printer',
        })
        cls.base64_image = base64.b64encode(b'test_image_data')

    def test_01_print_to_system_success(self):
        """Test successful printing simulation"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Success"
            mock_run.return_value.stderr = ""
            
            result = self.env['pos.config'].action_print_to_system(self.pos_config.id, self.base64_image)
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_02_print_to_system_failure(self):
        """Test failed printing simulation"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "Error"
            
            result = self.env['pos.config'].action_print_to_system(self.pos_config.id, self.base64_image)
            self.assertFalse(result)
            mock_run.assert_called_once()

    def test_03_print_to_system_exception(self):
        """Test exception during printing simulation"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Test exception")
            
            result = self.env['pos.config'].action_print_to_system(self.pos_config.id, self.base64_image)
            self.assertFalse(result)
            mock_run.assert_called_once()

    def test_04_print_to_system_no_printer(self):
        """Test print without configured printer"""
        self.pos_config.system_printer_name = False
        result = self.env['pos.config'].action_print_to_system(self.pos_config.id, self.base64_image)
        self.assertFalse(result)
