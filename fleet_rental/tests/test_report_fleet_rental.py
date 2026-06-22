# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestFleetRentalReport(TransactionCase):

    def test_select_and_group_by_include_contract_source_table(self):
        report = self.env['report.fleet.rental']

        select_query = report._select()
        group_by_query = report._group_by()

        self.assertIn('t.id as id', select_query)
        self.assertIn('t.customer_id as customer_id', select_query)
        self.assertIn('GROUP BY', group_by_query)
        self.assertIn('rent_start_date', group_by_query)

    def test_init_creates_report_view(self):
        self.env['report.fleet.rental'].init()

        self.env.cr.execute("SELECT to_regclass('report_fleet_rental')")
        self.assertEqual(self.env.cr.fetchone()[0], 'report_fleet_rental')
