# -*- coding: utf-8 -*-

from datetime import date
from unittest.mock import patch

from odoo.addons.mail.models.mail_template import MailTemplate
from odoo.tests.common import TransactionCase

from ..models import hr_employee


class TestWorkAnniversaryReminder(TransactionCase):
    """Test the automated work-anniversary reminder."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = date(2030, 6, 15)

    def _create_employee(self, name, contract_date_start=False):
        return self.env['hr.employee'].create({
            'name': name,
            'date_version': contract_date_start or self.today,
            'contract_date_start': contract_date_start,
            'wage': 1,
        })

    def test_cron_sends_reminder_for_completed_anniversary(self):
        employee = self._create_employee(
            'Anniversary Employee', date(2029, 6, 15),
        )
        sent_reminders = []

        def send_mail(template, res_id, force_send=False, **kwargs):
            sent_reminders.append((res_id, force_send))

        with patch.object(
            hr_employee.fields.Date, 'today', return_value=self.today,
        ), patch.object(
            MailTemplate, MailTemplate.send_mail.__name__, new=send_mail,
        ):
            self.env['hr.employee']._cron_anniversary_reminder()

        self.assertEqual(sent_reminders, [(employee.id, True)])

    def test_cron_skips_employees_without_completed_anniversary(self):
        self._create_employee('No Start Date')
        self._create_employee('Future Start Date', date(2031, 6, 15))
        self._create_employee('Not Anniversary Date', date(2029, 6, 16))
        self._create_employee('First Day Employee', self.today)
        sent_reminders = []

        def send_mail(template, res_id, force_send=False, **kwargs):
            sent_reminders.append((res_id, force_send))

        with patch.object(
            hr_employee.fields.Date, 'today', return_value=self.today,
        ), patch.object(
            MailTemplate, MailTemplate.send_mail.__name__, new=send_mail,
        ):
            self.env['hr.employee']._cron_anniversary_reminder()

        self.assertFalse(sent_reminders)
