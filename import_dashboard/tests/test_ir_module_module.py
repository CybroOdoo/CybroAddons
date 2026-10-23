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
#############################################################################

from unittest.mock import patch

from odoo.addons.base.models.ir_module import IrModuleModule as BaseIrModule
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrModuleModule(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Module = self.env['ir.module.module']
        self.ConfigParam = self.env['ir.config_parameter']

    def test_button_uninstall_side_effects(self):
        """Test that uninstalling a module turns off its import flag"""
        module = self.Module.search([('name', '=', 'mrp')], limit=1)
        if not module:
            module = self.Module.create({
                'name': 'mrp',
                'state': 'installed',
                'shortdesc': 'MRP'
            })
        elif module.state != 'installed':
            # enabling the BoM import requires mrp to be installed
            module.state = 'installed'

        self.ConfigParam.set_bool('import_dashboard.import_bom', True)

        # Patch the base method so the module is not really uninstalled
        with patch.object(BaseIrModule, 'button_uninstall', return_value=True):
            module.button_uninstall()

        self.assertFalse(self.ConfigParam.get_bool('import_dashboard.import_bom'))
