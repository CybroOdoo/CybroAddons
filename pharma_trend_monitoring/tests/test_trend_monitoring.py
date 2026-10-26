# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
import zipfile
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class TrendCommon(PharmaTestCommon):
    """A tablet product whose finished-goods Assay (95–105) is watched."""

    @classmethod
    def setUpClass(cls):
        """Approve a specification that watches the Assay."""
        super().setUpClass()
        cls.Parameter = cls.env['pharma.trend.parameter']
        cls.qa_only = cls.env['res.users'].create({
            'name': 'QA Only', 'login': 'pharma_trend_qa_only',
            'group_ids': [(4, cls.env.ref('pharmaceutical_base.group_pharma_role_qa').id),
                          (4, cls.env.ref('stock.group_stock_user').id)],
        })
        cls.tmpl = cls.env['product.template'].create({
            'name': 'Paracetamol Tablets', 'is_storable': True, 'tracking': 'lot',
        })
        cls.tab_spec = cls.watched_spec(cls.tmpl, 95.0, 105.0)
        cls.param = cls.Parameter.search([('product_id', '=', cls.tmpl.id)])
        cls.lot_seq = 0

    @classmethod
    def watched_spec(cls, template, low, high):
        """Approve a finished-goods specification with a watched Assay."""
        spec = cls.create_spec(template, 'finished', low, high)
        spec.parameter_ids.is_trended = True
        spec.action_submit_review()
        spec.with_user(cls.qa_user).action_approve()
        return spec

    def started_order(self, value=None, template=None):
        """A test order in progress, with ``value`` entered when given."""
        template = template or self.tmpl
        type(self).lot_seq += 1
        lot = self.create_lot(template.product_variant_id, 'TAB-%s' % self.lot_seq)
        order = self.create_order(lot=lot, stage='finished', template=template)
        order.action_start_test()
        if value is not None:
            order.result_line_ids.write({'actual_value': value})
        return order

    def passed_order(self, value, template=None):
        """A test order with ``value`` entered and approved by QA."""
        order = self.started_order(value, template)
        order.with_user(self.qa_user).action_approve()
        self.assertEqual(order.status, 'passed')
        return order


@tagged('post_install', '-at_install')
class TestWatchedParameter(TrendCommon):
    """The watch tick and the parameter it creates."""

    def test_watch_tick(self):
        """Only quantitative parameters can be watched, and only in draft."""
        spec = self.create_spec(self.tmpl, 'incoming', 0.0, 0.0)
        with self.assertRaises(ValidationError):
            spec.parameter_ids.is_trended = True
        spec = self.create_spec(self.tmpl, 'incoming')
        spec.parameter_ids.is_trended = True
        spec.parameter_ids.is_trended = False
        with self.assertRaises(ValidationError):
            self.tab_spec.parameter_ids.write({'is_trended': False})
        self.tab_spec.parameter_ids.write({'is_trended': True})

    def test_parameter_from_spec(self):
        """Approving the specification starts the history; a new version updates it."""
        param = self.param
        self.assertEqual(len(param), 1)
        self.assertEqual(
            (param.state, param.is_trended, param.spec_min, param.spec_max, param.spec_line_id),
            ('collecting', True, 95.0, 105.0, self.tab_spec.parameter_ids))
        self.assertEqual(param.name, 'Paracetamol Tablets / Assay (Finished Goods)')
        self.assertEqual((param.result_count, param.min_history, param.flagged_count), (0, 2, 0))
        # A second version with the parameter renamed in case and spacing keeps one history.
        spec = self.create_spec(self.tmpl, 'finished', 96.0, 104.0)
        spec.parameter_ids.write({'parameter_name': ' assay ', 'is_trended': True})
        spec.action_submit_review()
        spec.with_user(self.qa_user).action_approve()
        self.assertEqual(self.Parameter.search_count([('product_id', '=', self.tmpl.id)]), 1)
        self.assertEqual((param.spec_min, param.spec_line_id), (96.0, spec.parameter_ids))
        # A version without the parameter stops watching it.
        spec = self.create_spec(self.tmpl, 'finished')
        spec.parameter_ids.parameter_name = 'Dissolution'
        spec.action_submit_review()
        spec.with_user(self.qa_user).action_approve()
        self.assertFalse(param.is_trended)
        self.assertEqual(self.Parameter._pharma_get_or_create(spec.parameter_ids, self.env.company).parameter_key,
                         'dissolution')

    def test_access(self):
        """Pharma users read the history; nobody sets a range by hand."""
        self.assertEqual(self.param.with_user(self.operator).name, self.param.name)
        with self.assertRaises(AccessError):
            self.Parameter.with_user(self.qa_user).create({
                'product_id': self.tmpl.id, 'stage': 'finished',
                'parameter_name': 'X', 'parameter_key': 'x'})
        with self.assertRaises(UserError):
            self.param.write({'range_low': 1.0})


@tagged('post_install', '-at_install')
class TestNormalRange(TrendCommon):
    """Approving the normal range, flagging and the batch hold."""

    def approve(self, user=None):
        """QA approves the range from the results so far."""
        self.param.with_user(user or self.qa_only).action_approve_range()

    def test_approval_rules(self):
        """QA only, enough results, and some variation."""
        self.passed_order(100.0)
        with self.assertRaises(AccessError):
            self.approve(self.operator)
        with self.assertRaises(UserError):
            self.approve()
        self.passed_order(100.0)
        with self.assertRaises(UserError):
            self.approve()
        self.assertEqual(self.param.state, 'collecting')

    def test_flag_and_hold(self):
        """A result outside the range holds the order until QA reviews it."""
        before = self.started_order(104.0)
        for value in (99.0, 100.0, 101.0):
            self.passed_order(value)
        self.assertFalse(before.outside_normal_range)
        self.approve()
        param = self.param
        self.assertEqual(param.state, 'active')
        self.assertEqual((param.range_mean, param.range_std_dev, param.range_sample_count),
                         (100.0, 1.0, 3))
        self.assertEqual((param.range_low, param.range_high), (97.0, 103.0))
        self.assertEqual(param.range_approved_by, self.qa_only)
        self.assertIn('Normal range approved by QA Only', param.message_ids[0].body)
        # The order still under test is checked against the new range.
        self.assertTrue(before.outside_normal_range)

        inside, outside = self.started_order(102.0), self.started_order(104.0)
        self.assertFalse(inside.outside_normal_range)
        line = outside.result_line_ids
        self.assertEqual((line.outside_normal_range, line.normal_range_applied,
                          line.normal_range_low, line.normal_range_high),
                         (True, True, 97.0, 103.0))
        self.assertEqual(param.flagged_count, 2)
        with self.assertRaises(ValidationError):
            outside.with_user(self.qa_user).action_approve()
        with self.assertRaises(AccessError):
            outside.with_user(self.operator).write({'normal_range_note': 'Looks fine'})
        with self.assertRaises(ValidationError):
            outside.with_user(self.qa_user).write({'normal_range_reviewed': True})
        outside.with_user(self.qa_user).write({
            'normal_range_note': 'New API supplier lot; within specification.',
            'normal_range_reviewed': True,
        })
        outside.with_user(self.qa_user).action_approve()
        self.assertEqual(outside.status, 'passed')

        action = param.action_view_flagged_orders()
        self.assertEqual(self.env['pharma.qc.test.order'].search(action['domain']),
                         before | outside)

    def test_reapproval_keeps_history(self):
        """Re-approval moves the range for open orders only and logs both ranges."""
        for value in (99.0, 100.0, 101.0):
            self.passed_order(value)
        self.approve()
        closed = self.started_order(104.0)
        closed.with_user(self.qa_user).write({'normal_range_note': 'Reviewed.', 'normal_range_reviewed': True})
        closed.with_user(self.qa_user).action_approve()
        still_open = self.started_order(104.0)
        self.env.company.pharma_trend_range_sigma = 10.0
        self.approve()
        param = self.param
        # Wider range, held inside the specification.
        self.assertEqual((param.range_low, param.range_high, param.range_sample_count),
                         (95.0, 105.0, 4))
        self.assertIn('Old range: 97.0000 – 103.0000', param.message_ids[0].body)
        closed_line, open_line = closed.result_line_ids, still_open.result_line_ids
        self.assertEqual((closed_line.outside_normal_range, closed_line.normal_range_high),
                         (True, 103.0))
        self.assertEqual((open_line.outside_normal_range, open_line.normal_range_high),
                         (False, 105.0))
        self.assertFalse(still_open.outside_normal_range)

    def test_chart_and_report(self):
        """The chart data, the actions and the trend summary report."""
        for value in (99.0, 100.0, 101.0):
            self.passed_order(value)
        param = self.param
        data = param.get_chart_data()
        self.assertEqual((data['state'], data['range'], len(data['points'])), ('collecting', False, 3))
        self.assertEqual(data['spec'], {'min': 95.0, 'max': 105.0})
        self.approve()
        data = param.get_chart_data(limit=2)
        self.assertEqual([p['value'] for p in data['points']], [100.0, 101.0])
        self.assertEqual(data['range']['low'], 97.0)
        self.assertEqual(param.action_open_chart()['params'], {'trend_parameter_id': param.id})
        self.assertEqual(param.action_open_apqr_export()['context']['default_product_id'], self.tmpl.id)
        stats = param._pharma_report_stats()
        self.assertEqual((stats['count'], stats['mean'], stats['min'], stats['max']),
                         (3, 100.0, 99.0, 101.0))
        html = self.env['ir.actions.report']._render_qweb_html(
            'pharma_trend_monitoring.action_report_pharma_trend_summary', param.ids)[0]
        self.assertIn(b'Trend Summary', html)
        self.assertIn(b'97.0000', html)
        empty = self.watched_spec(self.env['product.template'].create({'name': 'Syrup'}), 1.0, 2.0)
        stats = self.Parameter.search([('spec_line_id', '=', empty.parameter_ids.id)])._pharma_report_stats()
        self.assertEqual((stats['count'], stats['mean'], stats['std_dev']), (0, 0.0, 0.0))

    def test_settings(self):
        """At least two results and a positive width."""
        company = self.env.company
        for value in (1, 0):
            with self.assertRaises(ValidationError):
                company.pharma_trend_min_history = value
        for value in (-1.0, 0.0):
            with self.assertRaises(ValidationError):
                company.pharma_trend_range_sigma = value
        settings = self.env['res.config.settings'].create({'pharma_trend_min_history': 5})
        settings.execute()
        self.assertEqual(company._pharma_trend_settings()['pharma_trend_min_history'], 5)


@tagged('post_install', '-at_install')
class TestApqrExport(TrendCommon):
    """The APQR trending workbook."""

    def wizard(self, **vals):
        """The export dialog for the tablets."""
        return self.env['pharma.trend.apqr.export'].with_user(self.qa_only).create(
            dict({'product_id': self.tmpl.id}, **vals))

    def test_export(self):
        """A summary sheet and one sheet per parameter, with the period applied."""
        for value in (99.0, 100.0, 101.0):
            self.passed_order(value)
        self.param.with_user(self.qa_only).action_approve_range()
        order = self.started_order(104.0)
        order.with_user(self.qa_user).write({'normal_range_note': 'Reviewed.', 'normal_range_reviewed': True})
        order.with_user(self.qa_user).action_approve()
        wizard = self.wizard()
        action = wizard.action_export()
        self.assertIn('field=file_data', action['url'])
        self.assertTrue(wizard.file_name.startswith('APQR_Trending_Paracetamol_Tablets_'))
        book = zipfile.ZipFile(io.BytesIO(base64.b64decode(wizard.file_data)))
        workbook = book.read('xl/workbook.xml').decode()
        self.assertIn('name="Summary"', workbook)
        self.assertIn('name="Assay"', workbook)
        self.assertTrue(any(name.startswith('xl/charts/') for name in book.namelist()))
        lines = wizard._period_results(self.param)
        self.assertEqual(len(lines), 4)
        self.assertEqual(wizard._ranges_applied(lines), [(97.0, 103.0)])
        # A period without results still exports, with no chart.
        past = self.wizard(date_from=fields.Date.today() - timedelta(days=30),
                           date_to=fields.Date.today() - timedelta(days=20),
                           parameter_ids=[(6, 0, self.param.ids)])
        past.action_export()
        self.assertFalse(past._period_results(self.param))
        self.assertFalse(any(name.startswith('xl/charts/') for name in zipfile.ZipFile(
            io.BytesIO(base64.b64decode(past.file_data))).namelist()))

    def test_export_refused(self):
        """A reversed period or a product with nothing watched is refused."""
        with self.assertRaises(UserError):
            self.wizard(date_from=fields.Date.today(),
                        date_to=fields.Date.today() - timedelta(days=1)).action_export()
        other = self.env['product.template'].create({'name': 'Unwatched'})
        with self.assertRaises(UserError):
            self.wizard(product_id=other.id).action_export()
        with self.assertRaises(AccessError):
            self.env['pharma.trend.apqr.export'].with_user(self.operator).create({'product_id': self.tmpl.id})

    def test_helpers(self):
        """Sheet names are valid and unique; another product drops chosen parameters."""
        Export = self.env['pharma.trend.apqr.export']
        used = {'summary'}
        self.assertEqual(Export._sheet_name('Assay [HPLC]: a/b', used), 'Assay  HPLC   a b')
        self.assertEqual(Export._sheet_name('Assay [HPLC]: a/b', used), 'Assay  HPLC   a b (2)')
        self.assertEqual(Export._sheet_name('', used), 'Parameter')
        self.assertEqual(len(Export._sheet_name('x' * 40, used)), 31)
        form = Form(Export.with_user(self.qa_only))
        form.product_id = self.tmpl
        form.parameter_ids.add(self.param)
        form.product_id = self.env['product.template'].create({'name': 'Syrup'})
        self.assertFalse(form.parameter_ids)
