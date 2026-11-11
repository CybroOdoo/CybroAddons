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
#############################################################################
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestMasterData(SalonCommon):
    """Services, stages, holidays, working hours, partner/user extensions
    and the data files shipped with the module."""

    def test_service_defaults_and_fields(self):
        service = self.env['salon.service'].create(
            {'name': 'Massage', 'price': 80.0})
        self.assertEqual(service.currency_id,
                         self.env.company.currency_id)
        self.assertEqual(service.price, 80.0)
        self.assertEqual(service.time_taken, 0.0)

    def test_service_requires_name_and_price(self):
        with self.assertRaises((IntegrityError, ValidationError)), \
                mute_logger('odoo.sql_db'):
            self.env['salon.service'].create({'price': 10.0})

    def test_stage_ordering(self):
        stages = self.env['salon.stage'].search([])
        self.assertEqual(stages.mapped('sequence'),
                         sorted(stages.mapped('sequence')))
        new_stage = self.env['salon.stage'].create({'name': 'Custom'})
        self.assertEqual(new_stage.sequence, 1)

    def test_demo_stages(self):
        self.assertEqual(self.stages.mapped('name'),
                         ['Draft', 'Open', 'Invoiced', 'Closed', 'Cancelled'])

    def test_holiday_demo_data(self):
        if not self.env.ref('salon_management.salon_holiday_01',
                            raise_if_not_found=False):
            self.skipTest("Salon demo data is not loaded")
        sunday = self.env.ref('salon_management.salon_holiday_01')
        monday = self.env.ref('salon_management.salon_holiday_02')
        self.assertTrue(sunday.holiday)
        self.assertFalse(monday.holiday)
        self.assertEqual(len(self.env['salon.holiday'].search([])), 7)

    def test_working_hours_defaults(self):
        hours = self.env['salon.working.hours'].create({'name': 'Custom'})
        self.assertEqual(hours.from_time, '9:00 AM')
        self.assertEqual(hours.to_time, '6:00 PM')
        hours.write({'from_time': '12:30 AM', 'to_time': '11:30 PM'})
        self.assertEqual(hours.from_time, '12:30 AM')

    def test_working_hours_selection(self):
        selection = self.env['salon.working.hours']._fields[
            'from_time'].selection
        values = [value for value, _label in selection]
        self.assertEqual(len(values), 48)
        for expected in ('12:00 AM', '9:00 AM', '12:00 PM', '1:30 PM',
                         '11:30 PM'):
            self.assertIn(expected, values)

    def test_working_hours_demo_data(self):
        if not self.env.ref('salon_management.salon_working_01',
                            raise_if_not_found=False):
            self.skipTest("Salon demo data is not loaded")
        self.assertEqual(self.env['salon.working.hours'].search_count([
            ('id', 'in', [self.env.ref(
                'salon_management.salon_working_0%d' % i).id
                for i in range(1, 8)])]), 7)

    def test_partner_and_user_extensions(self):
        self.assertFalse(self.customer.partner_salon)
        self.customer.partner_salon = True
        self.assertTrue(self.customer.partner_salon)
        self.assertFalse(self.env.user.user_salon_active)
        default = self.env.ref('salon_management.res_partner_01')
        self.assertEqual(default.name, 'Salon Default Customer')

    def test_chair_user_marks_active_salon_user(self):
        user_a = self.env['res.users'].create(
            {'name': 'A', 'login': 'salon_a'})
        user_b = self.env['res.users'].create(
            {'name': 'B', 'login': 'salon_b'})
        chair = self.env['salon.chair'].create({
            'date': self.at(),
            'user_line': [(0, 0, {'user_id': user_a.id,
                                  'start_date': self.at()})],
        })
        self.assertTrue(user_a.user_salon_active)
        self.assertFalse(user_b.user_salon_active)
        line = chair.user_line
        self.assertTrue(line.read_only_checker)

    def test_data_files_loaded(self):
        for xmlid in (
                'salon_management.mail_template_salon_request_received',
                'salon_management.mail_template_salon_approved',
                'salon_management.mail_template_salon_rejected',
                'salon_management.ir_cron_collections_today',
                'salon_management.salon_chair_sequence',
                'salon_management.salon_order_sequence',
                'salon_management.salon_management_client_action',
                'salon_management.website_menu_salon_booking',
                'salon_management.salon_service_product_01'):
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False),
                            xmlid)
        menu = self.env.ref('salon_management.website_menu_salon_booking')
        self.assertEqual(menu.url, '/salon_booking_form')
        client = self.env.ref(
            'salon_management.salon_management_client_action')
        self.assertEqual(client.tag, 'salon_dashboard')

    def test_security_groups(self):
        user_group = self.env.ref('salon_management.group_salon_user')
        manager_group = self.env.ref('salon_management.group_salon_manager')
        self.assertIn(user_group, manager_group.implied_ids)
        self.assertIn(self.env.ref('base.group_user'),
                      user_group.implied_ids)
