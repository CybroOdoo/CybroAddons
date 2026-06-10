# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################from .common import TestChequeCommon

class TestChequeFormat(TestChequeCommon):

    def test_cheque_format_action_print_test(self):
        """Test action_print_test on cheque.format"""
        result = self.cheque_format.action_print_test()
        self.assertIn(result.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
        if result.get('type') == 'ir.actions.report':
            self.assertEqual(result.get('report_name'), 'odoo_print_cheque.cheque_test_print')
