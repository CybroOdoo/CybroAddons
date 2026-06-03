# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestAccountMoveReportSql(TransactionCase):

    def test_select_appends_margin_field(self):
        sql = self.env['account.invoice.report']._select().replace('\n', ' ')

        self.assertIn(", line.margin_amount as margin_amount", sql)
