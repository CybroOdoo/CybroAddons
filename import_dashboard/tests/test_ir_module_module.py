# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from unittest.mock import patch

class TestIrModuleModule(TransactionCase):

    def setUp(self):
        super(TestIrModuleModule, self).setUp()
        self.Module = self.env['ir.module.module']
        self.ConfigParam = self.env['ir.config_parameter']

    def test_button_uninstall_side_effects(self):
        """Test that uninstalling a module turns off its import flag"""
        # Mocking the name to 'mrp' and calling button_uninstall
        # We need to find or create a dummy module record
        module = self.Module.create({
            'name': 'mrp',
            'state': 'installed',
            'shortdesc': 'MRP'
        })
        
        self.ConfigParam.set_param('import_bom', True)
        
        # We mock super().button_uninstall to avoid actual uninstallation
        with patch.object(type(self.env['ir.module.module']), 'button_uninstall', lambda x: True):
            module.button_uninstall()
            
        self.assertFalse(self.ConfigParam.get_param('import_bom'))
