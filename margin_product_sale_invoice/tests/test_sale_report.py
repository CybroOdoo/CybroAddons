# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestSaleReportSql(TransactionCase):

    def test_select_sale_appends_margin_field(self):
        sql = self.env['sale.report']._select_sale().replace('\n', ' ')

        self.assertIn(
            "SUM(l.margin_amount_sale / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) AS margin_sale",
            sql,
        )
