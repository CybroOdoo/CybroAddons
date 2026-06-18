# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.exceptions import UserError

class TestHrHolidayGenerator(TransactionCase):

    def setUp(self):
        super(TestHrHolidayGenerator, self).setUp()
        self.country = self.env.ref('base.in')
        self.wizard_model = self.env['hr.holiday.generator']
        
        # Setup API Key in config
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_holiday_generator.holiday_api_key', 'test_api_key')

    def test_action_generate_success(self):
        """Test successful holiday generation with mocked API"""
        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })

        mock_response = {
            'response': {
                'holidays': [
                    {
                        'name': 'Test Holiday 1',
                        'description': 'Description 1',
                        'date': {'iso': '2025-01-01'}
                    },
                    {
                        'name': 'Test Holiday 2',
                        'description': 'Description 2',
                        'date': {'iso': '2025-05-01'}
                    }
                ]
            }
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            wizard.action_generate()

            self.assertEqual(len(wizard.calender_leaves_ids), 2)
            self.assertEqual(wizard.calender_leaves_ids[0].name, 'Test Holiday 1')
            self.assertEqual(wizard.calender_leaves_ids[0].start_date.date().strftime('%Y-%m-%d'), '2025-01-01')

    def test_action_generate_no_api_key(self):
        """Test UserError when API key is missing"""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_holiday_generator.holiday_api_key', False)
        
        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })

        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_action_save_no_overlap(self):
        """Test action_save when there are no existing overlaps"""
        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })
        
        # Manually populate transient leaves
        wizard.calender_leaves_ids = [
            (0, 0, {
                'name': 'Holiday 1',
                'start_date': '2025-01-01 00:00:00',
                'end_date': '2025-01-01 23:59:59',
                'description': 'Desc 1'
            })
        ]

        # Ensure no existing resource calendar leaves for this date
        self.env['resource.calendar.leaves'].search([
            ('date_from', '>=', '2025-01-01 00:00:00'),
            ('date_to', '<=', '2025-01-01 23:59:59'),
            ('resource_id', '=', False)
        ]).unlink()

        wizard.action_save()

        # Verify resource.calendar.leaves created
        leave = self.env['resource.calendar.leaves'].search([
            ('name', '=', 'Holiday 1'),
            ('date_from', '=', '2025-01-01 00:00:00')
        ])
        self.assertTrue(leave)

    def test_action_save_with_overlap(self):
        """Test action_save with overlapping dates"""
        # Create an existing holiday
        self.env['resource.calendar.leaves'].create({
            'name': 'Existing Holiday',
            'date_from': '2025-01-01 00:00:00',
            'date_to': '2025-01-01 23:59:59',
        })

        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })
        
        wizard.calender_leaves_ids = [
            (0, 0, {
                'name': 'New Overlapping Holiday',
                'start_date': '2025-01-01 00:00:00',
                'end_date': '2025-01-01 23:59:59',
                'description': 'Desc Overlap'
            })
        ]

        result = wizard.action_save()

        # Verify OverlappingDate wizard is returned
        self.assertEqual(result['res_model'], 'overlapping.date')
        
        # Verify holiday.log was created
        log = self.env['holiday.log'].search([
            ('name', '=', 'New Overlapping Holiday')
        ])
        self.assertTrue(log)

    def test_duplicate_date_warning(self):
        """Test warning when two holidays fall on the same date"""
        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })
        
        wizard.calender_leaves_ids = [
            (0, 0, {
                'name': 'Holiday A',
                'start_date': '2025-01-01 00:00:00',
                'end_date': '2025-01-01 23:59:59',
            }),
            (0, 0, {
                'name': 'Holiday B',
                'start_date': '2025-01-01 00:00:00',
                'end_date': '2025-01-01 23:59:59',
            })
        ]

        result = wizard.action_save()
        
        # Should return overlapping.date wizard due to same date holidays
        self.assertEqual(result['res_model'], 'overlapping.date')
        
        warning_wizard = self.env['overlapping.date'].browse(result['res_id'])
        self.assertIn('Select only one holiday per date', warning_wizard.warning)

    def test_overlapping_date_action_continue(self):
        """Test action_continue in overlapping.date wizard"""
        # Create an existing holiday
        self.env['resource.calendar.leaves'].create({
            'name': 'Existing',
            'date_from': '2025-01-01 00:00:00',
            'date_to': '2025-01-01 23:59:59',
        })

        wizard = self.wizard_model.create({
            'country_id': self.country.id,
            'generation_mode': 'year',
            'year': '2025',
        })
        
        holiday_existing = self.env['calendar.leave'].create({
            'holiday_generator_id': wizard.id,
            'name': 'Existing One',
            'start_date': '2025-01-01 00:00:00',
            'end_date': '2025-01-01 23:59:59',
        })
        holiday_new = self.env['calendar.leave'].create({
            'holiday_generator_id': wizard.id,
            'name': 'New One',
            'start_date': '2025-02-01 00:00:00',
            'end_date': '2025-02-01 23:59:59',
        })

        warning_wizard = self.env['overlapping.date'].create({
            'warning': 'Test Warning'
        })

        # Mock context as if it was opened from action_save
        ctx = {'active_id': wizard.id}
        result = warning_wizard.with_context(ctx).action_continue()

        self.assertEqual(result['res_model'], 'calendar.leave.generator')
        # Check if default_calendar_leave_ids contains only 'New One'
        # filtered_calendar_leaves filters out cl.start_date.date() IN existing_public_holidays
        filtered_ids = result['context']['default_calendar_leave_ids']
        self.assertIn(holiday_new.id, filtered_ids)
        self.assertNotIn(holiday_existing.id, filtered_ids)

    def test_calendar_leave_generator_action_generate(self):
        """Test final generation from calendar.leave.generator"""
        leave_gen = self.env['calendar.leave.generator'].create({})
        leave_gen.calendar_leave_ids = [
            (0, 0, {
                'name': 'Final Holiday',
                'start_date': '2025-03-01 00:00:00',
                'end_date': '2025-03-01 23:59:59',
            })
        ]

        leave_gen.action_generate()

        leave = self.env['resource.calendar.leaves'].search([
            ('name', '=', 'Final Holiday'),
            ('date_from', '=', '2025-03-01 00:00:00')
        ])
        self.assertTrue(leave)
