# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.addons.ent_hr_zk_attendance.tests.common import EntZkTransactionCase


class TestZkReportDailyAttendance(EntZkTransactionCase):
    def test_init_recreates_sql_view(self):
        model = self.env["zk.report.daily.attendance"]

        with patch("odoo.addons.ent_hr_zk_attendance.models.zk_report_daily_attendance.tools.drop_view_if_exists") as drop_view, patch.object(
            model.env.cr, "execute"
        ) as execute:
            model.init()

        drop_view.assert_called_once_with(model.env.cr, "zk_report_daily_attendance")
        execute.assert_called_once()
        self.assertIn("create or replace view zk_report_daily_attendance", execute.call_args.args[0].lower())
