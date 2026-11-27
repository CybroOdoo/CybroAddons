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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged, users

from odoo.addons.base.tests.common import BaseCommon


@tagged('post_install', '-at_install')
class TestProductBatchReport(BaseCommon):
    """Tests for the lot and serial number expiry report wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.now = fields.Datetime.now()
        cls.product_a = cls._create_product('Batch Product A')
        cls.product_b = cls._create_product('Batch Product B')
        cls.lot_expired = cls._create_lot(cls.product_a, 'LOT-EXPIRED', -5)
        cls.lot_old = cls._create_lot(cls.product_a, 'LOT-OLD', -60)
        cls.lot_soon = cls._create_lot(cls.product_a, 'LOT-SOON', 10)
        cls.lot_late = cls._create_lot(cls.product_b, 'LOT-LATE', 90)
        cls.lot_empty = cls.env['stock.lot'].create({
            'name': 'LOT-EMPTY',
            'product_id': cls.product_b.id,
            'expiration_date': cls.now + timedelta(days=5),
        })
        cls.stock_manager = cls.env['res.users'].create({
            'name': 'Stock Manager',
            'login': 'batch_stock_manager',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('stock.group_stock_manager').id,
            ])],
        })
        cls.stock_user = cls.env['res.users'].create({
            'name': 'Stock User',
            'login': 'batch_stock_user',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('stock.group_stock_user').id,
            ])],
        })
        cls.basic_user = cls.env['res.users'].create({
            'name': 'Basic User',
            'login': 'batch_basic_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    @classmethod
    def _create_product(cls, name):
        """Create a lot tracked product that uses expiration dates."""
        return cls.env['product.product'].create({
            'name': name,
            'is_storable': True,
            'tracking': 'lot',
            'use_expiration_date': True,
        })

    @classmethod
    def _create_lot(cls, product, name, days):
        """Create a lot expiring in ``days`` days with one unit in stock."""
        lot = cls.env['stock.lot'].create({
            'name': name,
            'product_id': product.id,
            'expiration_date': cls.now + timedelta(days=days),
        })
        cls.env['stock.quant']._update_available_quantity(
            product, cls.env.ref('stock.stock_location_stock'), 1, lot_id=lot)
        return lot

    def _wizard(self, vals=None):
        """Create a wizard as an inventory administrator."""
        return self.env['product.batch.report'].with_user(
            self.stock_manager).create(vals or {})

    def _lot_names(self, wizard):
        """Return the lot names that the wizard puts in the report."""
        return [line['lot_name']
                for line in wizard._prepare_report_data()['values']]

    def test_expired_report(self):
        """Expired lots are listed, lots in the future are not."""
        wizard = self._wizard(
            {'expiry_type': 'expired'})
        names = self._lot_names(wizard)
        self.assertIn('LOT-EXPIRED', names)
        self.assertIn('LOT-OLD', names)
        self.assertNotIn('LOT-SOON', names)

    def test_expired_within_days(self):
        """The Within field limits how far back expired lots go."""
        wizard = self._wizard(
            {'expiry_type': 'expired', 'expiry_days': 30})
        names = self._lot_names(wizard)
        self.assertIn('LOT-EXPIRED', names)
        self.assertNotIn('LOT-OLD', names)

    def test_going_to_expire_report(self):
        """Lots that expire in the future are listed."""
        wizard = self._wizard(
            {'expiry_type': 'expire'})
        names = self._lot_names(wizard)
        self.assertIn('LOT-SOON', names)
        self.assertIn('LOT-LATE', names)
        self.assertNotIn('LOT-EXPIRED', names)

    def test_going_to_expire_within_days(self):
        """The Within field limits how far ahead expiring lots go."""
        wizard = self._wizard(
            {'expiry_type': 'expire', 'expiry_days': 30})
        names = self._lot_names(wizard)
        self.assertIn('LOT-SOON', names)
        self.assertNotIn('LOT-LATE', names)

    def test_lots_without_stock_are_skipped(self):
        """A lot without any quantity on hand is not reported."""
        wizard = self._wizard(
            {'expiry_type': 'expire'})
        self.assertNotIn('LOT-EMPTY', self._lot_names(wizard))

    def test_product_wise_filter(self):
        """Product wise mode groups lots and honours the product filter."""
        wizard = self._wizard({
            'tracking_wise': 'product_wise',
            'expiry_type': 'expire',
            'product_ids': [(6, 0, self.product_b.ids)],
        })
        data = wizard._prepare_report_data()
        self.assertEqual(data['heading'], [self.product_b.display_name])
        self.assertEqual([line['lot_name'] for line in data['values']],
                         ['LOT-LATE'])

    def test_product_wise_without_product_lists_all(self):
        """Without a product filter every product is listed."""
        wizard = self._wizard(
            {'tracking_wise': 'product_wise', 'expiry_type': 'expire'})
        data = wizard._prepare_report_data()
        self.assertEqual(len(data['heading']), 2)

    def test_lot_wise_has_no_heading(self):
        """Lot wise mode has no product headings."""
        wizard = self._wizard(
            {'expiry_type': 'expire'})
        self.assertEqual(wizard._prepare_report_data()['heading'], [])

    def test_negative_days_refused(self):
        """A negative number of days is refused."""
        with self.assertRaises(ValidationError):
            self._wizard({'expiry_days': -1})

    def test_generate_report_action(self):
        """The wizard returns the PDF report action with the data."""
        wizard = self._wizard(
            {'expiry_type': 'expired'})
        action = wizard.generate_pdf_report()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(
            action['report_name'],
            'product_batch_report.product_batch_report_template')
        names = [line['lot_name'] for line in action['data']['values']]
        self.assertIn('LOT-EXPIRED', names)

    def test_generate_report_without_result(self):
        """An empty result raises a clear error."""
        wizard = self._wizard({
            'expiry_type': 'expired',
            'tracking_wise': 'product_wise',
            'product_ids': [(6, 0, self.product_b.ids)],
        })
        with self.assertRaises(UserError):
            wizard.generate_pdf_report()

    def test_report_renders(self):
        """The QWeb template renders in both modes."""
        for tracking in ('tracking_wise', 'product_wise'):
            for expiry in ('expired', 'expire'):
                wizard = self._wizard(
                    {'tracking_wise': tracking, 'expiry_type': expiry})
                data = wizard._prepare_report_data()
                report = self.env.ref(
                    'product_batch_report.product_batch_report_action_report')
                html, _ = report._render_qweb_html(
                    report.report_name, wizard.ids, data=data)
                self.assertIn(b'Lot/Serial Number Expiry Report', html)
                if expiry == 'expired':
                    self.assertIn(b'Expired Since', html)
                else:
                    self.assertIn(b'Expires In', html)

    def test_date_range_without_days(self):
        """Without days the report is open ended on one side."""
        wizard = self._wizard(
            {'expiry_type': 'expired'})
        date_from, date_to = wizard._get_date_range()
        self.assertFalse(date_from)
        self.assertTrue(date_to)
        wizard.expiry_type = 'expire'
        date_from, date_to = wizard._get_date_range()
        self.assertTrue(date_from)
        self.assertFalse(date_to)

    def test_date_range_header_is_open_ended(self):
        """A side without a limit has no date in the report header."""
        data = self._wizard({'expiry_type': 'expired'})._prepare_report_data()
        self.assertEqual(data['date_from'], '')
        self.assertTrue(data['date_to'])
        data = self._wizard({'expiry_type': 'expire'})._prepare_report_data()
        self.assertTrue(data['date_from'])
        self.assertEqual(data['date_to'], '')

    def test_date_range_header_with_days(self):
        """With a number of days both sides of the header have a date."""
        data = self._wizard(
            {'expiry_type': 'expired', 'expiry_days': 10},
        )._prepare_report_data()
        self.assertTrue(data['date_from'])
        self.assertTrue(data['date_to'])

    def test_open_ended_header_renders_no_limit(self):
        """The printed header says "No limit" for an open ended side."""
        wizard = self._wizard({'expiry_type': 'expired'})
        report = self.env.ref(
            'product_batch_report.product_batch_report_action_report')
        html, _ = report._render_qweb_html(
            report.report_name, wizard.ids,
            data=wizard._prepare_report_data())
        self.assertIn(b'No limit', html)

    def test_expired_days_are_whole_days_elapsed(self):
        """A lot that expired five days ago is reported as 5 days."""
        wizard = self._wizard({'expiry_type': 'expired'})
        lines = {line['lot_name']: line['expiry_days']
                 for line in wizard._prepare_report_data()['values']}
        self.assertEqual(lines['LOT-EXPIRED'], '5 Days')
        self.assertEqual(lines['LOT-OLD'], '60 Days')

    @users('batch_stock_manager')
    def test_stock_manager_can_use_wizard(self):
        """An inventory administrator can create the wizard and print."""
        wizard = self.env['product.batch.report'].create(
            {'expiry_type': 'expire'})
        self.assertTrue(wizard.generate_pdf_report())

    @users('batch_stock_user')
    def test_stock_user_refused(self):
        """An inventory user without administrator rights is refused."""
        with self.assertRaises(AccessError):
            self.env['product.batch.report'].create({})

    def test_menu_is_restricted_to_stock_managers(self):
        """The report menu is limited to inventory administrators."""
        menu = self.env.ref('product_batch_report.product_batch_report_menu')
        self.assertEqual(
            menu.group_ids, self.env.ref('stock.group_stock_manager'))

    @users('batch_basic_user')
    def test_basic_user_refused(self):
        """A user without inventory rights cannot use the wizard."""
        with self.assertRaises(AccessError):
            self.env['product.batch.report'].create({})

    def test_timezone_formatting(self):
        """Dates are formatted in the time zone of the user."""
        wizard = self._wizard().with_context(tz='Asia/Kolkata')
        value = wizard._format_date(
            fields.Datetime.to_datetime('2026-01-01 00:00:00'))
        self.assertEqual(value, '2026-01-01 05:30:00')
