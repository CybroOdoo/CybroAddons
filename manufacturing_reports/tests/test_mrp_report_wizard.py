# -*- coding: utf-8 -*-
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
import io
import json
from unittest.mock import Mock
from PIL import Image

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes


@tagged('post_install', '-at_install')
class TestMrpReportWizard(TransactionCase):
    """Test cases for 'mrp.report.wizard' model in manufacturing_reports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        img_io = io.BytesIO()
        Image.new('RGB', (10, 10), '#ffffff').save(img_io, 'PNG')
        test_image = BinaryBytes(img_io.getvalue())

        cls.product = cls.env['product.product'].create({
            'name': 'Test MRP Product',
            'type': 'consu',
            'image_1920': test_image,
        })
        cls.product_no_image = cls.env['product.product'].create({
            'name': 'Test Product No Image',
            'type': 'consu',
            'image_1920': False,
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
        })
        cls.mo = cls.env['mrp.production'].create({
            'product_id': cls.product.id,
            'bom_id': cls.bom.id,
            'product_qty': 5.0,
            'user_id': cls.env.user.id,
            'date_start': fields.Datetime.now(),
        })
        cls.mo_no_image = cls.env['mrp.production'].create({
            'product_id': cls.product_no_image.id,
            'product_qty': 2.0,
            'user_id': cls.env.user.id,
            'date_start': fields.Datetime.now(),
        })

    def test_onchange_filter_user(self):
        """Test onchange_filter_user resets responsible_ids only when filter_user is False."""
        admin_user = self.env.ref('base.user_admin')
        wizard = self.env['mrp.report.wizard'].new({
            'filter_user': True,
            'responsible_ids': [Command.link(admin_user.id)],
        })
        # 1. When filter_user is True, onchange keeps responsible_ids
        wizard.onchange_filter_user()
        self.assertTrue(wizard.responsible_ids)

        # 2. When filter_user is False, onchange clears responsible_ids
        wizard.filter_user = False
        wizard.onchange_filter_user()
        self.assertFalse(wizard.responsible_ids)

    def test_onchange_filter_date(self):
        """Test onchange_filter_date resets date_from only when filter_date is False."""
        wizard = self.env['mrp.report.wizard'].new({
            'filter_date': True,
            'date_from': fields.Date.today(),
        })
        # 1. When filter_date is True, onchange keeps date_from
        wizard.onchange_filter_date()
        self.assertTrue(wizard.date_from)

        # 2. When filter_date is False, onchange clears date_from
        wizard.filter_date = False
        wizard.onchange_filter_date()
        self.assertFalse(wizard.date_from)

    def test_check_report(self):
        """Test check_report returns xlsx action or raises UserError if empty."""
        # 1. Matching manufacturing orders exist
        wizard = self.env['mrp.report.wizard'].create({
            'product_ids': [Command.link(self.product.id)],
        })
        action = wizard.check_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')
        data_block = action.get('data', {})
        self.assertEqual(data_block.get('model'), 'mrp.report.wizard')
        self.assertEqual(data_block.get('output_format'), 'xlsx')
        options = json.loads(data_block.get('options', '{}'))
        self.assertTrue(options.get('mrp'))
        self.assertEqual(options['mrp'][0]['product'], self.product.name)

        # 2. No matching manufacturing orders -> raises UserError
        empty_wizard = self.env['mrp.report.wizard'].create({
            'state': 'cancel',
        })
        with self.assertRaises(UserError):
            empty_wizard.check_report()

    def test_print_pdf_with_image(self):
        """Test print_pdf with products containing images."""
        wizard = self.env['mrp.report.wizard'].with_context(discard_logo_check=True).create({
            'product_ids': [Command.link(self.product.id)],
        })
        action = wizard.print_pdf()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'manufacturing_reports.report_mrp_order')
        report_data = action.get('data', {})
        self.assertTrue(report_data.get('mrp'))
        self.assertTrue(report_data['mrp'][0].get('image'))

    def test_print_pdf_without_image(self):
        """Test print_pdf handles products without images without crashing."""
        wizard = self.env['mrp.report.wizard'].with_context(discard_logo_check=True).create({
            'product_ids': [Command.link(self.product_no_image.id)],
        })
        action = wizard.print_pdf()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'manufacturing_reports.report_mrp_order')
        report_data = action.get('data', {})
        self.assertTrue(report_data.get('mrp'))
        self.assertFalse(report_data['mrp'][0].get('image'))

    def test_print_pdf_empty_raises(self):
        """Test print_pdf raises UserError when no data matches."""
        empty_wizard = self.env['mrp.report.wizard'].create({
            'state': 'cancel',
        })
        with self.assertRaises(UserError):
            empty_wizard.print_pdf()

    def test_print_pdf_state_filter(self):
        """Test print_pdf builds state filter as single label string instead of order list."""
        wizard = self.env['mrp.report.wizard'].with_context(discard_logo_check=True).create({
            'state': 'draft',
        })
        action = wizard.print_pdf()
        report_data = action.get('data', {})
        self.assertEqual(report_data.get('state'), 'Draft')

    def test_get_xlsx_report(self):
        """Test get_xlsx_report writes binary Excel content to response stream."""
        wizard = self.env['mrp.report.wizard'].create({})
        data = {
            'date_from': '2026-01-01',
            'state': 'Draft',
            'mrp': [{
                'name': self.mo.name,
                'product': self.product.name,
                'quantity': 5.0,
                'unit': self.product.uom_id.name,
                'responsible': self.env.user.name,
                'start_date': str(self.mo.date_start),
                'state': 'Draft',
            }],
        }
        response_stream = io.BytesIO()
        response = Mock(stream=response_stream)

        # 1. Valid data creates Excel content
        wizard.get_xlsx_report(data, response)
        self.assertGreater(len(response_stream.getvalue()), 0)

        # 2. Empty data raises UserError
        with self.assertRaises(UserError):
            wizard.get_xlsx_report({}, response)
