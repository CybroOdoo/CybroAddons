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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestAccountMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env['account.account'].search([], limit=1)
        cls.journal = cls.env['account.journal'].search([('type', '=', 'sale')], limit=1)

    def test_reconcile_with_skip_flag(self):
        """Test reconciliation is skipped when skip_pos_invoice_reconciliation is in context."""
        if not self.journal or not self.account:
            return  # Skip test if accounting environment is incomplete
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'move_type': 'entry',
        })
        line = self.env['account.move.line'].create({
            'name': 'Test Line',
            'move_id': move.id,
            'account_id': self.account.id,
        })
        # Test default reconcile behavior with skip flag returns True
        res = line.with_context(skip_pos_invoice_reconciliation=True).reconcile()
        self.assertTrue(res)
