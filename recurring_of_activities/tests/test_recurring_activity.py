# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

import logging
from datetime import date, timedelta
from unittest.mock import PropertyMock, patch

from dateutil.relativedelta import relativedelta

from odoo.exceptions import MissingError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestRecurringActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("Setting up TestRecurringActivity class")

        cls.test_partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.activity_type = cls.env['mail.activity.type'].create({
            'name': 'Test Recurring Activity Type',
        })

        cls.user = cls.env.user

        _logger.info("Setup completed successfully")

    def test_01_archive_date_validation(self):
        """Test validation error when archive date is before create date."""
        _logger.info("Starting test_01_archive_date_validation")

        try:
            with self.assertRaises(ValidationError):
                _logger.info("Attempting to create recurring activity with past archive date")
                _logger.info("start_date: %s | archive_date: %s",
                             date.today(),
                             date.today() - timedelta(days=5))

                self.env['recurring.activity'].create({
                    'name': 'Test Past Archive Date',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Test Summary',
                    'action': f'res.partner,{self.test_partner.id}',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() - timedelta(days=5),
                })

                _logger.warning("WARNING: No ValidationError was raised — validation may not be working!")

            _logger.info("test_01_archive_date_validation PASSED — ValidationError raised as expected")

        except AssertionError as e:
            _logger.error("test_01_archive_date_validation FAILED — ValidationError was NOT raised")
            _logger.error("AssertionError: %s", e)
            raise

        except Exception as e:
            _logger.error("test_01_archive_date_validation encountered unexpected error: %s", e)
            raise

    def test_02_missing_action_validation(self):
        """Test validation error when action is missing."""
        _logger.info("Starting test_02_missing_action_validation")

        try:
            with self.assertRaises(Exception):
                _logger.info("Attempting to create recurring activity without action field")
                _logger.info("start_date: %s | archive_date: %s",
                             date.today(),
                             date.today() + timedelta(days=5))

                self.env['recurring.activity'].create({
                    'name': 'Test Missing Action',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Test Summary',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() + timedelta(days=5),
                })

                _logger.warning("WARNING: No Exception was raised — action field validation may not be working!")

            _logger.info("test_02_missing_action_validation PASSED — Exception raised as expected")

        except AssertionError as e:
            _logger.error("test_02_missing_action_validation FAILED — Exception was NOT raised")
            _logger.error("AssertionError: %s", e)
            raise

        except Exception as e:
            _logger.error("test_02_missing_action_validation encountered unexpected error: %s", e)
            raise

    def test_03_daily_recurring_activity(self):
        """Test daily recurring activity creation and calculation."""
        _logger.info("Starting test_03_daily_recurring_activity")

        try:
            _logger.info("Attempting to create daily recurring activity")
            _logger.info("start_date: %s | archive_date: %s | period: day",
                         date.today(),
                         date.today() + timedelta(days=10))

            recurring = self.env['recurring.activity'].create({
                'name': 'Daily Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Daily Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'day',
                'start_date': date.today(),
                'archive_date': date.today() + timedelta(days=10),
            })

            _logger.info("Recurring activity created successfully — ID: %s | Name: %s",
                         recurring.id, recurring.name)

            self.assertTrue(recurring.id, "Recurring activity was not created")
            _logger.info("test_03_daily_recurring_activity PASSED — record created with ID: %s", recurring.id)

        except AssertionError as e:
            _logger.error("test_03_daily_recurring_activity FAILED — assertion error")
            _logger.error("AssertionError: %s", e)
            raise

        except Exception as e:
            _logger.error("test_03_daily_recurring_activity encountered unexpected error: %s", e)
            raise

        self.assertEqual(
            recurring.next_activity_date,
            date.today(),
            "Next activity date should be today for daily",
        )

        activity = self.env['mail.activity'].search([
            ('summary', '=', 'Daily Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertTrue(activity, "Mail activity should have been created")
        _logger.info("test_03_daily_recurring_activity successfull")

    def test_04_weekly_recurring_activity(self):
        """Test weekly recurring activity creation and calculation."""
        _logger.info("Starting test_04_weekly_recurring_activity")

        try:
            today = date.today()
            weekdays = ['monday', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            today_weekday = weekdays[today.weekday()]

            _logger.info("Today: %s | Weekday: %s | Weekday field: %s",
                         today, today.strftime("%A"), today_weekday)

            vals = {
                'name': 'Weekly Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Weekly Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'week',
                'start_date': today,
                'archive_date': today + timedelta(days=14),
            }
            vals[today_weekday] = True

            _logger.info("Attempting to create weekly recurring activity with vals: %s", vals)

            recurring = self.env['recurring.activity'].create(vals)

            _logger.info("Recurring activity created successfully — ID: %s | Name: %s",
                         recurring.id, recurring.name)
            _logger.info("Expected next_activity_date: %s | Actual next_activity_date: %s",
                         today.strftime("%Y-%m-%d"), recurring.next_activity_date)

            self.assertEqual(
                recurring.next_activity_date,
                today,
                "Next activity date should match today for weekly",
            )

            _logger.info("test_04_weekly_recurring_activity PASSED — next_activity_date matched: %s",
                         recurring.next_activity_date)

        except AssertionError as e:
            _logger.error("test_04_weekly_recurring_activity FAILED — next_activity_date mismatch")
            _logger.error("AssertionError: %s", e)
            raise

        except Exception as e:
            _logger.error("test_04_weekly_recurring_activity encountered unexpected error: %s", e)
            raise

    def test_05_monthly_recurring_activity_first(self):
        """Test monthly recurring activity (first day of month)."""
        _logger.info("Starting test_05_monthly_recurring_activity_first")

        try:
            _logger.info("Attempting to create monthly recurring activity with month_by: first")
            _logger.info("start_date: %s | archive_date: %s",
                         date.today(),
                         date.today() + relativedelta(months=2))

            recurring = self.env['recurring.activity'].create({
                'name': 'Monthly First Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Monthly First Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'month',
                'month_by': 'first',
                'start_date': date.today(),
                'archive_date': date.today() + relativedelta(months=2),
            })

            _logger.info("Recurring activity created — ID: %s | Name: %s",
                         recurring.id, recurring.name)

            expected_date = (date.today() + relativedelta(months=1)).replace(day=1)

            _logger.info("Expected next_activity_date: %s | Actual: %s",
                         expected_date, recurring.next_activity_date)

            self.assertEqual(recurring.next_activity_date, expected_date)

            _logger.info("test_05_monthly_recurring_activity_first PASSED — next_activity_date matched: %s",
                         recurring.next_activity_date)

        except AssertionError as e:
            _logger.error("test_05_monthly_recurring_activity_first FAILED — next_activity_date mismatch")
            _logger.error("Expected: %s | Got: %s",
                          (date.today() + relativedelta(months=1)).replace(day=1),
                          recurring.next_activity_date)
            _logger.error("AssertionError: %s", e)
            raise

        except Exception as e:
            _logger.error("test_05_monthly_recurring_activity_first encountered unexpected error: %s", e)
            raise

    def test_06_yearly_recurring_activity(self):
        """Test yearly recurring activity for both upcoming and already-passed dates."""
        _logger.info("Starting test_06_yearly_recurring_activity")
        today = date.today()

        # Case 1: Target date is later in the current year (December 25)
        rec_future = self.env['recurring.activity'].create({
            'name': 'Yearly Future Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Yearly Future Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'year',
            'year_months': '12',
            'year_date': 25,
            'start_date': today,
            'archive_date': today + relativedelta(years=3),
        })
        if today <= date(today.year, 12, 25):
            expected_future = date(today.year, 12, 25)
        else:
            expected_future = date(today.year + 1, 12, 25)
        self.assertEqual(rec_future.next_activity_date, expected_future)
        self.assertGreaterEqual(rec_future.next_activity_date, today)

        # Case 2: Target date has already passed in the current year (January 10)
        rec_past = self.env['recurring.activity'].create({
            'name': 'Yearly Past Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Yearly Past Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'year',
            'year_months': '1',
            'year_date': 10,
            'start_date': today,
            'archive_date': today + relativedelta(years=3),
        })
        if today <= date(today.year, 1, 10):
            expected_past = date(today.year, 1, 10)
        else:
            expected_past = date(today.year + 1, 1, 10)
        self.assertEqual(rec_past.next_activity_date, expected_past)
        self.assertGreater(rec_past.next_activity_date, today, "Must advance to next year when date has passed")
        _logger.info("test_06_yearly_recurring_activity PASSED")

    def test_07_uninstalled_model_validation(self):
        """Test validation error when choosing an uninstalled model."""
        _logger.info("Starting test_07_uninstalled_model_validation")
        uninstalled_model = next(
            (m for m in ['purchase.order', 'sale.order', 'crm.lead', 'project.task', 'uninstalled.fake.model'] if m not in self.env),
            'uninstalled.fake.model',
        )
        # Check that check_model_installed returns False for uninstalled model
        self.assertFalse(self.env['recurring.activity'].check_model_installed(uninstalled_model))
        self.assertTrue(self.env['recurring.activity'].check_model_installed('res.partner'))

        # Attempt to create recurring activity with uninstalled model should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Test Uninstalled Model',
                'activity_type_id': self.activity_type.id,
                'summary': 'Test Summary',
                'action': f'{uninstalled_model},1',
                'period': 'day',
                'start_date': date.today(),
                'archive_date': date.today() + timedelta(days=5),
            })
        self.assertIn("The module is not installed, so we can't configure any records for this.", str(cm.exception))
        _logger.info("test_07_uninstalled_model_validation PASSED — validation error raised as expected")

    def test_08_multi_record_creation(self):
        """Test multi-record creation via @api.model_create_multi."""
        _logger.info("Starting test_08_multi_record_creation")
        uninstalled_model = next(
            (m for m in ['purchase.order', 'sale.order', 'crm.lead', 'project.task', 'uninstalled.fake.model'] if m not in self.env),
            'uninstalled.fake.model',
        )

        # 1. Test empty vals_list
        empty_recs = self.env['recurring.activity'].create([])
        self.assertFalse(empty_recs, "Creating with empty vals_list should return empty recordset")

        # 2. Test batch creation of multiple records
        vals_list = [
            {
                'name': 'Batch Activity 1',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Summary 1',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'day',
                'start_date': date.today(),
                'archive_date': date.today() + timedelta(days=10),
            },
            {
                'name': 'Batch Activity 2',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Summary 2',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'day',
                'start_date': date.today(),
                'archive_date': date.today() + timedelta(days=10),
            },
        ]
        recs = self.env['recurring.activity'].create(vals_list)
        self.assertEqual(len(recs), 2, "Both recurring activity records should be created")
        for rec in recs:
            self.assertEqual(rec.next_activity_date, date.today(), "Next activity date should be set for each record")

        # Check mail activities for both records
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
            ('summary', 'in', ['Batch Summary 1', 'Batch Summary 2']),
        ])
        self.assertEqual(len(activities), 2, "Mail activity should be created for each record in the batch")

        # 3. Test batch creation failure when one record is missing action
        with self.assertRaises(ValidationError):
            self.env['recurring.activity'].create([
                {
                    'name': 'Valid Batch Rec',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Valid Batch Rec Summary',
                    'action': f'res.partner,{self.test_partner.id}',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() + timedelta(days=5),
                },
                {
                    'name': 'Invalid Batch Rec No Action',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Invalid Batch Rec Summary',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() + timedelta(days=5),
                },
            ])

        # 4. Test batch creation failure when one record has uninstalled model
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create([
                {
                    'name': 'Valid Batch Rec',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Valid Batch Rec Summary',
                    'action': f'res.partner,{self.test_partner.id}',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() + timedelta(days=5),
                },
                {
                    'name': 'Invalid Batch Rec Uninstalled',
                    'activity_type_id': self.activity_type.id,
                    'summary': 'Invalid Batch Rec Summary',
                    'action': f'{uninstalled_model},1',
                    'period': 'day',
                    'start_date': date.today(),
                    'archive_date': date.today() + timedelta(days=5),
                },
            ])
        self.assertIn("The module is not installed, so we can't configure any records for this.", str(cm.exception))

        _logger.info("test_08_multi_record_creation PASSED")

    def test_09_deleted_reference_cron_run(self):
        """Test that cron run does not crash with MissingError when a referenced record does not exist or is deleted."""
        _logger.info("Starting test_09_deleted_reference_cron_run")
        partner_ref = 'res.partner,999999'
        rec = self.env['recurring.activity'].create({
            'name': 'Test Deleted Partner Recurring Activity',
            'activity_type_id': self.activity_type.id,
            'summary': 'Summary For Temp Partner',
            'action': partner_ref,
            'period': 'day',
            'start_date': date.today(),
            'archive_date': date.today() + timedelta(days=10),
        })
        self.assertTrue(rec.id)

        # The cron run create_recurring_activities() should gracefully skip the deleted/missing record without MissingError
        self.env['recurring.activity'].create_recurring_activities()
        _logger.info("test_09_deleted_reference_cron_run PASSED — no MissingError raised")

    def test_10_weekly_recurring_no_weekday_validation(self):
        """Test validation error when period is week but no weekday is selected."""
        _logger.info("Starting test_10_weekly_recurring_no_weekday_validation")
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Weekly No Weekday Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Weekly No Weekday Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'week',
                'start_date': date.today(),
                'archive_date': date.today() + timedelta(days=14),
            })
        self.assertIn("Please choose a specific day for the recurring activity.", str(cm.exception))
        _logger.info("test_10_weekly_recurring_no_weekday_validation PASSED")

    def test_11_weekly_recurring_multiple_weekdays(self):
        """Test weekly recurring activity with multiple weekdays and verify _get_weekdays."""
        _logger.info("Starting test_11_weekly_recurring_multiple_weekdays")
        today = date.today()
        # Test helper method directly
        temp_rec = self.env['recurring.activity'].new({
            'monday': True,
            'wed': True,
            'fri': True,
        })
        self.assertEqual(temp_rec._get_weekdays(), ['Mon', 'Wed', 'Fri'])

        all_days_rec = self.env['recurring.activity'].new({
            'monday': True,
            'tue': True,
            'wed': True,
            'thu': True,
            'fri': True,
            'sat': True,
            'sun': True,
        })
        self.assertEqual(all_days_rec._get_weekdays(), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

        # Create record with multiple weekdays (including today to ensure immediate next activity)
        weekday_fields = ['monday', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        today_field = weekday_fields[today.weekday()]
        other_field = weekday_fields[(today.weekday() + 2) % 7]

        vals = {
            'name': 'Weekly Multi Days Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Weekly Multi Days Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'week',
            'start_date': today,
            'archive_date': today + timedelta(days=21),
        }
        vals[today_field] = True
        vals[other_field] = True

        rec = self.env['recurring.activity'].create(vals)
        self.assertEqual(str(rec.next_activity_date), today.strftime("%Y-%m-%d"))

        # Verify next recurring dates include dates for both weekdays
        next_dates = rec._get_next_recurring_dates()
        self.assertGreater(len(next_dates), 1, "Should calculate multiple occurrences across archive window")
        for nd in next_dates:
            self.assertIsInstance(nd, date, "Weekly branch must return date instances, not strings")
        _logger.info("test_11_weekly_recurring_multiple_weekdays PASSED")

    def test_12_weekly_recurring_future_weekday(self):
        """Test weekly recurring activity when the chosen weekday is later in the week."""
        _logger.info("Starting test_12_weekly_recurring_future_weekday")
        today = date.today()
        weekday_fields = ['monday', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        tomorrow = today + timedelta(days=1)
        tomorrow_field = weekday_fields[tomorrow.weekday()]

        vals = {
            'name': 'Weekly Future Day Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Weekly Future Day Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'week',
            'start_date': today,
            'archive_date': today + timedelta(days=14),
        }
        vals[tomorrow_field] = True

        rec = self.env['recurring.activity'].create(vals)
        self.assertEqual(str(rec.next_activity_date), tomorrow.strftime("%Y-%m-%d"))
        _logger.info("test_12_weekly_recurring_future_weekday PASSED")

    def test_13_monthly_recurring_last_day(self):
        """Test monthly recurring activity configured for the last day of the month."""
        _logger.info("Starting test_13_monthly_recurring_last_day")
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Monthly Last Day Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Monthly Last Day Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'month',
            'month_by': 'last',
            'start_date': today,
            'archive_date': today + relativedelta(months=3),
        })

        last_day_current_month = today.replace(day=1) + relativedelta(months=1, days=-1)
        expected_date = last_day_current_month

        self.assertEqual(rec.next_activity_date, expected_date)

        # Verify mail activity was created with the last day of month deadline
        activity = self.env['mail.activity'].search([
            ('summary', '=', 'Monthly Last Day Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertTrue(activity, "Mail activity should be created for monthly last day")
        self.assertEqual(activity.date_deadline, expected_date)
        _logger.info("test_13_monthly_recurring_last_day PASSED")

    def test_14_monthly_recurring_date_of_month(self):
        """Test monthly recurring activity configured for a specific date of month."""
        _logger.info("Starting test_14_monthly_recurring_date_of_month")
        today = date.today()

        # Case 1: Target date in current month (upcoming or today)
        target_day_future = 28 if today.day <= 28 else today.day
        rec_future = self.env['recurring.activity'].create({
            'name': 'Monthly Future Date Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Monthly Future Date Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'month',
            'month_by': 'date',
            'date_of_month': target_day_future,
            'start_date': today,
            'archive_date': today + relativedelta(months=3),
        })
        expected_date_future = today + relativedelta(day=target_day_future)
        self.assertEqual(rec_future.next_activity_date, expected_date_future)
        self.assertGreaterEqual(rec_future.next_activity_date, today)

        # Case 2: Target date has passed in current month (advances to next month)
        if today.day > 1:
            target_day_past = 1
            expected_date_past = today + relativedelta(months=1, day=target_day_past)
            rec_past = self.env['recurring.activity'].create({
                'name': 'Monthly Past Date Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Monthly Past Date Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'month',
                'month_by': 'date',
                'date_of_month': target_day_past,
                'start_date': today,
                'archive_date': today + relativedelta(months=3),
            })
            self.assertEqual(rec_past.next_activity_date, expected_date_past)
            self.assertGreater(
                rec_past.next_activity_date,
                today,
                "Must advance to next month when date of month has passed",
            )
        _logger.info("test_14_monthly_recurring_date_of_month PASSED")

    def test_15_monthly_recurring_invalid_date_validation(self):
        """Test validation error when date_of_month is invalid (e.g. 32)."""
        _logger.info("Starting test_15_monthly_recurring_invalid_date_validation")
        today = date.today()
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Monthly Invalid Date Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Monthly Invalid Date Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'month',
                'month_by': 'date',
                'date_of_month': 32,
                'start_date': today,
                'archive_date': today + relativedelta(months=2),
            })
        self.assertIn("Invalid date of the month specified", str(cm.exception))
        _logger.info("test_15_monthly_recurring_invalid_date_validation PASSED")

    def test_16_monthly_recurring_invalid_month_by_validation(self):
        """Test validation error when month_by is not set or invalid."""
        _logger.info("Starting test_16_monthly_recurring_invalid_month_by_validation")
        today = date.today()
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Monthly Invalid MonthBy Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Monthly Invalid MonthBy Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'month',
                'month_by': False,
                'start_date': today,
                'archive_date': today + relativedelta(months=2),
            })
        self.assertIn("Please select a recurring activity type for the month.", str(cm.exception))
        _logger.info("test_16_monthly_recurring_invalid_month_by_validation PASSED")

    def test_17_yearly_missing_date_or_month_validation(self):
        """Test validation error when year_date or year_months is missing."""
        _logger.info("Starting test_17_yearly_missing_date_or_month_validation")
        today = date.today()
        # Missing year_months
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Yearly Missing Month Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Yearly Missing Month Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'year',
                'year_date': 15,
                'start_date': today,
                'archive_date': today + relativedelta(years=2),
            })
        self.assertIn("Both Date and month are required for yearly recurrence.", str(cm.exception))

        # Missing year_date
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Yearly Missing Date Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Yearly Missing Date Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'year',
                'year_months': '6',
                'start_date': today,
                'archive_date': today + relativedelta(years=2),
            })
        self.assertIn("Both Date and month are required for yearly recurrence.", str(cm.exception))

        # Invalid year_date (> 31)
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Yearly Invalid Date Test',
                'activity_type_id': self.activity_type.id,
                'summary': 'Yearly Invalid Date Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'year',
                'year_months': '6',
                'year_date': 32,
                'start_date': today,
                'archive_date': today + relativedelta(years=2),
            })
        self.assertIn("Invalid date of the month specified.", str(cm.exception))
        _logger.info("test_17_yearly_missing_date_or_month_validation PASSED")

    def test_18_yearly_past_month_next_year(self):
        """Test yearly recurring activity when target month has already passed in current year."""
        _logger.info("Starting test_18_yearly_past_month_next_year")
        today = date.today()
        past_month = 1
        rec = self.env['recurring.activity'].create({
            'name': 'Yearly Past Month Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Yearly Past Month Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'year',
            'year_months': str(past_month),
            'year_date': 10,
            'start_date': today,
            'archive_date': today + relativedelta(years=3),
        })

        if today.month <= past_month:
            expected_year = today.year
        else:
            expected_year = today.year + 1

        expected_date = date(expected_year, past_month, 10)
        self.assertEqual(rec.next_activity_date, expected_date)
        _logger.info("test_18_yearly_past_month_next_year PASSED")

    def test_19_archive_date_equal_today(self):
        """Test recurrence when current_date >= archive_date falls back to archive_date."""
        _logger.info("Starting test_19_archive_date_equal_today")
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Archive Date Equal Today Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Archive Date Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today,
        })
        self.assertEqual(rec.next_activity_date, today)
        _logger.info("test_19_archive_date_equal_today PASSED")

    def test_20_action_passed_as_recordset(self):
        """Test creating recurring activity by passing recordset object directly as action."""
        _logger.info("Starting test_20_action_passed_as_recordset")
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Recordset Action Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Recordset Action Summary',
            'action': self.test_partner,
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=10),
        })
        self.assertTrue(rec.id)
        self.assertEqual(rec.action, self.test_partner)

        activity = self.env['mail.activity'].search([
            ('summary', '=', 'Recordset Action Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertTrue(activity, "Mail activity should be created when action is passed as recordset")
        _logger.info("test_20_action_passed_as_recordset PASSED")

    def test_21_cron_trigger_and_execution(self):
        """Test the automated recurring activity cron job execution and duplicate avoidance."""
        _logger.info("Starting test_21_cron_trigger_and_execution")
        cron = self.env.ref('recurring_of_activities.ir_cron_update_recurring_activity')
        self.assertTrue(cron, "Cron record should exist in xml data")
        self.assertEqual(cron.model_id.model, 'recurring.activity')

        today = date.today()

        # 1. Test archiving of expired recurring activity rules
        expired_rule = self.env['recurring.activity'].create({
            'name': 'Expired Rule To Archive',
            'activity_type_id': self.activity_type.id,
            'summary': 'Expired Rule Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today - timedelta(days=10),
            'archive_date': today - timedelta(days=1),
        })
        self.assertTrue(expired_rule.active)

        # 2. Test duplicate avoidance for daily rule across cron runs
        self.env['recurring.activity'].create({
            'name': 'Daily Cron Deduplication Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Daily Cron Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        daily_acts_before = self.env['mail.activity'].search([
            ('summary', '=', 'Daily Cron Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertEqual(len(daily_acts_before), 1, "Initial creation should produce exactly 1 activity")

        # 3. Test duplicate avoidance for weekly rule across cron runs
        weekdays = ['monday', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        today_weekday = weekdays[today.weekday()]
        weekly_vals = {
            'name': 'Weekly Cron Deduplication Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Weekly Cron Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'week',
            'start_date': today,
            'archive_date': today + timedelta(days=21),
            today_weekday: True,
        }
        self.env['recurring.activity'].create(weekly_vals)
        weekly_acts_before = self.env['mail.activity'].search([
            ('summary', '=', 'Weekly Cron Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertEqual(len(weekly_acts_before), 1, "Initial creation should produce exactly 1 activity")

        # 4. Test duplicate avoidance for monthly rule across cron runs
        self.env['recurring.activity'].create({
            'name': 'Monthly Cron Deduplication Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Monthly Cron Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'month',
            'month_by': 'first',
            'start_date': today,
            'archive_date': today + relativedelta(months=3),
        })
        monthly_acts_before = self.env['mail.activity'].search([
            ('summary', '=', 'Monthly Cron Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertEqual(len(monthly_acts_before), 1, "Initial creation should produce exactly 1 activity")

        # First cron run (same day as create)
        self.env['recurring.activity'].create_recurring_activities()

        self.assertFalse(expired_rule.active, "Expired rule should be archived (active=False)")

        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Daily Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Daily cron run must not duplicate activity for same deadline",
        )
        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Weekly Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Weekly rule must not accumulate duplicate activities",
        )
        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Monthly Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Monthly rule must not accumulate duplicate activities",
        )

        # Second cron run (simulating recurring daily cron executions)
        self.env['recurring.activity'].create_recurring_activities()

        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Daily Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Consecutive cron runs must never duplicate daily activities",
        )
        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Weekly Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Consecutive cron runs must never duplicate weekly activities",
        )
        self.assertEqual(
            self.env['mail.activity'].search_count([
                ('summary', '=', 'Monthly Cron Summary'),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.test_partner.id),
            ]),
            1,
            "Consecutive cron runs must never duplicate monthly activities",
        )

        _logger.info("Cron executed create_recurring_activities with duplicate avoidance verified")
        _logger.info("test_21_cron_trigger_and_execution PASSED")

    def test_22_activity_with_user_and_note(self):
        """Test that user_id and note are properly passed to mail.activity."""
        _logger.info("Starting test_22_activity_with_user_and_note")
        today = date.today()
        test_note = '<p>This is a test recurring note</p>'
        self.env['recurring.activity'].create({
            'name': 'User and Note Test',
            'activity_type_id': self.activity_type.id,
            'user_id': self.user.id,
            'summary': 'User and Note Summary',
            'note': test_note,
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })

        activity = self.env['mail.activity'].search([
            ('summary', '=', 'User and Note Summary'),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ])
        self.assertTrue(activity)
        self.assertEqual(activity.user_id, self.user)
        self.assertEqual(activity.note, test_note)
        _logger.info("test_22_activity_with_user_and_note PASSED")

    def test_23_regular_user_access(self):
        """Test standard internal user access rights (CRUD) for recurring.activity."""
        _logger.info("Starting test_23_regular_user_access")
        demo_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.user

        today = date.today()
        rec_as_user = self.env['recurring.activity'].with_user(demo_user).create({
            'name': 'Demo User Activity',
            'activity_type_id': self.activity_type.id,
            'summary': 'Demo User Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        self.assertTrue(rec_as_user.id)

        # Test read
        self.assertEqual(rec_as_user.with_user(demo_user).name, 'Demo User Activity')

        # Test write
        rec_as_user.with_user(demo_user).write({'summary': 'Updated Demo Summary'})
        self.assertEqual(rec_as_user.summary, 'Updated Demo Summary')

        # Test unlink
        rec_as_user.with_user(demo_user).unlink()
        self.assertFalse(rec_as_user.exists())
        _logger.info("test_23_regular_user_access PASSED")

    def test_24_defaults_and_copy(self):
        """Test default values and copy behavior for recurring.activity."""
        _logger.info("Starting test_24_defaults_and_copy")
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Defaults and Copy Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Defaults Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'archive_date': today + timedelta(days=10),
        })
        # Check default period is 'day'
        self.assertEqual(rec.period, 'day')
        # Check default month_by is 'date'
        self.assertEqual(rec.month_by, 'date')
        # Check default date_of_month is 1
        self.assertEqual(rec.date_of_month, 1)
        # Check default active is True
        self.assertTrue(rec.active)

        # Check action reference selection unique keys and hr.employee presence
        action_field = self.env['recurring.activity']._fields['action']
        sel_keys = [item[0] for item in action_field.selection]
        self.assertEqual(len(sel_keys), len(set(sel_keys)), "Reference selection keys must be unique")
        self.assertIn('hr.employee', sel_keys, "'hr.employee' should be present for Employees")

        # Test copy creates a new record
        copied_rec = rec.copy({'name': 'Copied Activity'})
        self.assertEqual(copied_rec.name, 'Copied Activity')
        self.assertEqual(copied_rec.action, rec.action)
        self.assertTrue(copied_rec.active)
        _logger.info("test_24_defaults_and_copy PASSED")

    def test_25_empty_recordset_and_archive_date_write(self):
        """Test empty recordset handling and archive date constraint validation on write."""
        _logger.info("Starting test_25_empty_recordset_and_archive_date_write")
        # 1. Empty recordset returns empty mail.activity
        empty_recs = self.env['recurring.activity']
        res = empty_recs.create_recurring_activities_record()
        self.assertFalse(res, "Empty recordset should return empty mail.activity recordset")

        # 2. Test constraint on write when archive_date < start_date
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Write Archive Date Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Write Archive Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=10),
        })
        with self.assertRaises(ValidationError) as cm:
            rec.write({'archive_date': rec.start_date - timedelta(days=2)})
        self.assertIn("The deadline should be greater than the created date", str(cm.exception))
        _logger.info("test_25_empty_recordset_and_archive_date_write PASSED")

    def test_26_batch_create_different_periods(self):
        """Test batch creating recurring activities with diverse periods."""
        _logger.info("Starting test_26_batch_create_different_periods")
        today = date.today()
        weekday_fields = ['monday', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        today_field = weekday_fields[today.weekday()]

        vals_list = [
            {
                'name': 'Batch Day Period',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Day Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'day',
                'start_date': today,
                'archive_date': today + timedelta(days=5),
            },
            {
                'name': 'Batch Week Period',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Week Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'week',
                today_field: True,
                'start_date': today,
                'archive_date': today + timedelta(days=14),
            },
            {
                'name': 'Batch Month Period',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Month Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'month',
                'month_by': 'first',
                'start_date': today,
                'archive_date': today + relativedelta(months=2),
            },
            {
                'name': 'Batch Year Period',
                'activity_type_id': self.activity_type.id,
                'summary': 'Batch Year Summary',
                'action': f'res.partner,{self.test_partner.id}',
                'period': 'year',
                'year_months': '12',
                'year_date': 31,
                'start_date': today,
                'archive_date': today + relativedelta(years=2),
            },
        ]
        recs = self.env['recurring.activity'].create(vals_list)
        self.assertEqual(len(recs), 4)
        for r in recs:
            self.assertTrue(r.next_activity_date, f"next_activity_date should be populated for {r.name}")
        _logger.info("test_26_batch_create_different_periods PASSED")

    def test_27_action_uninstalled_model_record_object(self):
        """Test ValidationError when action is an object whose _name is not installed."""
        _logger.info("Starting test_27_action_uninstalled_model_record_object")

        class FakeRecord:
            _name = 'uninstalled.fake.model'

        today = date.today()
        with self.assertRaises(ValidationError) as cm:
            self.env['recurring.activity'].create({
                'name': 'Test Object Uninstalled Model',
                'activity_type_id': self.activity_type.id,
                'summary': 'Test Summary',
                'action': FakeRecord(),
                'period': 'day',
                'start_date': today,
                'archive_date': today + timedelta(days=5),
            })
        self.assertIn(
            "The module is not installed, so we can't configure any records for this.",
            str(cm.exception),
        )
        _logger.info("test_27_action_uninstalled_model_record_object PASSED")

    def test_28_action_constrains_uninstalled_model_and_missing_error(self):
        """Test _check_action_model_installed constrains validation & exception."""
        _logger.info("Starting test_28_action_constrains_uninstalled_model")

        class FakeRecord:
            _name = 'uninstalled.fake.model'

        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Test Constrains Action Model',
            'activity_type_id': self.activity_type.id,
            'summary': 'Test Constrains Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        with patch.object(
            type(rec), 'action', new_callable=PropertyMock,
        ) as mock_action:
            mock_action.return_value = FakeRecord()
            with self.assertRaises(ValidationError):
                rec._check_action_model_installed()

            mock_action.side_effect = MissingError("Missing")
            rec._check_action_model_installed()

            mock_action.side_effect = KeyError("Key error")
            rec._check_action_model_installed()
        _logger.info("test_28_action_constrains_uninstalled_model PASSED")

    def test_29_create_recurring_activities_missing_error_fallback(self):
        """Test fallback loop when mail.activity batch create raises MissingError."""
        _logger.info("Starting test_29_create_recurring_activities_missing_error")
        today = date.today()
        rec1 = self.env['recurring.activity'].create({
            'name': 'Test MissingError 1',
            'activity_type_id': self.activity_type.id,
            'summary': 'Test MissingError Summary 1',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        rec2 = self.env['recurring.activity'].create({
            'name': 'Test MissingError 2',
            'activity_type_id': self.activity_type.id,
            'summary': 'Test MissingError Summary 2',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        recs = rec1 | rec2
        # Unlink the activities created during initial create so deduplication does not skip them
        self.env['mail.activity'].search([
            ('summary', 'in', ['Test MissingError Summary 1', 'Test MissingError Summary 2']),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
        ]).unlink()

        orig_create = self.env['mail.activity'].create
        call_count = 0

        def mock_create(vals):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call is batch create of both vals
                msg = "Batch missing"
                raise MissingError(msg)
            if call_count == 2:
                # Second call is individual create of val 1
                return orig_create(vals)
            # Third call is individual create of val 2
            msg = "Individual missing"
            raise MissingError(msg)

        with patch.object(
            type(self.env['mail.activity']), 'create', side_effect=mock_create,
        ):
            acts = recs.create_recurring_activities_record()
            self.assertTrue(acts)
        _logger.info("test_29_create_recurring_activities_missing_error PASSED")

    def test_30_empty_next_dates_and_error_handling(self):
        """Test handling when next recurring dates are empty or raise an error."""
        _logger.info("Starting test_30_empty_next_dates_and_error_handling")
        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Test Empty Next Dates',
            'activity_type_id': self.activity_type.id,
            'summary': 'Test Empty Dates Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'day',
            'start_date': today,
            'archive_date': today + timedelta(days=5),
        })
        # Test when _get_next_recurring_dates returns empty list
        with patch.object(type(rec), '_get_next_recurring_dates', return_value=[]):
            acts = rec.create_recurring_activities_record()
            self.assertFalse(acts)

        # Test when _get_next_recurring_dates raises ValueError
        with patch.object(
            type(rec), '_get_next_recurring_dates', side_effect=ValueError,
        ):
            acts = rec.create_recurring_activities_record()
            self.assertFalse(acts)
        _logger.info("test_30_empty_next_dates_and_error_handling PASSED")

    def test_31_monthly_last_day_next_month(self):
        """Test monthly recurring activity when current date is past end of month."""
        _logger.info("Starting test_31_monthly_last_day_next_month")

        class MockDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 5, 31)

            def replace(self, **kwargs):
                if kwargs.get('day') == 1:
                    return date(2026, 4, 1)
                return date.replace(self, **kwargs)

        today = date.today()
        rec = self.env['recurring.activity'].create({
            'name': 'Monthly Last Day Next Month Test',
            'activity_type_id': self.activity_type.id,
            'summary': 'Monthly Last Day Next Month Summary',
            'action': f'res.partner,{self.test_partner.id}',
            'period': 'month',
            'month_by': 'last',
            'start_date': today,
            'archive_date': today + relativedelta(months=6),
        })
        with patch(
            'odoo.addons.recurring_of_activities.models.recurring_activity.date',
            MockDate,
        ):
            next_dates = rec._get_next_recurring_dates()
            self.assertTrue(next_dates)
        _logger.info("test_31_monthly_last_day_next_month PASSED")
