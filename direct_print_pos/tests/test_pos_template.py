# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
#############################################################################

import logging
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestPosPrintTemplate(TransactionCase):
    """Test cases for the pos.print.template model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Template = cls.env['pos.print.template']
        cls.Template.search([]).unlink()
        cls.report = cls.env.ref(
            'direct_print_pos.action_report_pos_receipt_direct_print')

    def test_report_action_data(self):
        """The receipt report action is loaded for pos.order as a QWeb PDF."""
        self.assertEqual(self.report.model, 'pos.order')
        self.assertEqual(self.report.report_type, 'qweb-pdf')
        self.assertEqual(self.report.report_name,
                         'direct_print_pos.pos_receipt_template')
        logger.info('Passed : test_report_action_data')

    def test_create_template_defaults(self):
        """A new template is active and not default unless specified."""
        template = self.Template.create({'name': 'Receipt'})
        self.assertTrue(template.active)
        self.assertFalse(template.is_default)
        self.assertFalse(template.report_id)
        logger.info('Passed : test_create_template_defaults')

    def test_create_default_template(self):
        """A template can be flagged as the default and linked to a report."""
        template = self.Template.create({
            'name': 'Default Receipt',
            'report_id': self.report.id,
            'is_default': True,
        })
        self.assertTrue(template.is_default)
        self.assertEqual(template.report_id, self.report)
        logger.info('Passed : test_create_default_template')

    def test_multiple_non_default_templates(self):
        """Several non-default templates can coexist."""
        templates = self.Template.create([
            {'name': 'Receipt A'},
            {'name': 'Receipt B'},
        ])
        self.assertEqual(len(templates), 2)
        self.assertFalse(any(templates.mapped('is_default')))
        logger.info('Passed : test_multiple_non_default_templates')

    def test_single_default_template(self):
        """Setting a new default template demotes the previous default."""
        first = self.Template.create({'name': 'First', 'is_default': True})
        second = self.Template.create({'name': 'Second'})
        second.is_default = True
        self.assertTrue(second.is_default)
        self.assertFalse(first.is_default)
        self.assertEqual(
            self.Template.search_count([('is_default', '=', True)]), 1)
        logger.info('Passed : test_single_default_template')

    def test_archive_template(self):
        """Archived templates are hidden from default searches."""
        template = self.Template.create({'name': 'Archived'})
        template.active = False
        self.assertFalse(self.Template.search([('id', '=', template.id)]))
        self.assertTrue(self.Template.with_context(active_test=False).search(
            [('id', '=', template.id)]))
        logger.info('Passed : test_archive_template')
