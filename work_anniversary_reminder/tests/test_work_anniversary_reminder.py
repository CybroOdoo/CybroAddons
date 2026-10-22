# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Dilshad Tk (odoo@cybrosys.com)
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
###############################################################################
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import freeze_time


@tagged('post_install', '-at_install')
class TestWorkAnniversaryReminder(TransactionCase):

    def _create_employee(self, start):
        employee = self.env['hr.employee'].create({'name': 'Anniversary Test'})
        employee.write({'contract_date_start': start})
        return employee

    def _sent_employee_ids(self):
        Template = type(self.env['mail.template'])
        with patch.object(Template, 'send_mail', autospec=True) as send_mail:
            self.env['hr.employee']._cron_anniversary_reminder()
        return [call.args[1] for call in send_mail.call_args_list]

    def test_template_exists(self):
        self.assertTrue(self.env.ref(
            'work_anniversary_reminder.email_template_anniversary_reminder',
            raise_if_not_found=False))

    @freeze_time('2025-06-15')
    def test_mail_sent_on_anniversary(self):
        employee = self._create_employee('2020-06-15')
        self.assertIn(employee.id, self._sent_employee_ids())

    @freeze_time('2025-06-15')
    def test_mail_not_sent_on_other_day(self):
        employee = self._create_employee('2020-06-14')
        self.assertNotIn(employee.id, self._sent_employee_ids())

    @freeze_time('2025-06-15')
    def test_mail_not_sent_during_first_year(self):
        employee = self._create_employee('2025-06-15')
        self.assertNotIn(employee.id, self._sent_employee_ids())

    @freeze_time('2025-02-28')
    def test_february_29_celebrated_on_february_28_in_non_leap_year(self):
        employee = self._create_employee('2020-02-29')
        self.assertIn(employee.id, self._sent_employee_ids())

    @freeze_time('2024-02-29')
    def test_february_29_celebrated_on_february_29_in_leap_year(self):
        employee = self._create_employee('2020-02-29')
        self.assertIn(employee.id, self._sent_employee_ids())
