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
from lxml import etree

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import PharmaRetentionCommon


@tagged('post_install', '-at_install')
class TestRetentionConfiguration(PharmaRetentionCommon):
    """Retention locations, company default and product rule."""

    def test_location_count_and_action(self):
        """The location counts the samples it holds and lists them."""
        self.retained_sample()
        self.draft_sample(lot=self.released_lot(name='RS-LOT-2'))
        self.assertEqual(self.location.retention_sample_count, 1)
        action = self.location.action_view_retention_samples()
        self.assertEqual(action['domain'], [('location_id', '=', self.location.id)])

    def test_location_must_be_internal(self):
        """Only internal locations can be retention locations."""
        with self.assertRaises(ValidationError):
            self.env['stock.location'].create({
                'name': 'Bad', 'usage': 'view', 'pharma_is_retention_location': True,
            })

    def test_company_default_location(self):
        """Install creates and marks a default location; it must be a retention location."""
        company = self.env.company
        self.assertTrue(company.pharma_retention_location_id.pharma_is_retention_location)
        stock = self.warehouse.lot_stock_id
        with self.assertRaises(ValidationError):
            company.pharma_retention_location_id = stock
        company.pharma_retention_location_id = False
        self.env['res.company']._pharma_create_retention_locations()
        self.assertEqual(company.pharma_retention_location_id.name, 'Retention Samples')
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.pharma_retention_location_id,
                         company.pharma_retention_location_id)

    def test_product_rule(self):
        """Retention periods cannot be negative."""
        with self.assertRaises(ValidationError):
            self.product_tmpl.retention_period_months = -1

    def test_stock_user_without_pharma_role(self):
        """Inventory users outside the pharma roles still open batches and locations."""
        stock_user = self.env['res.users'].create({
            'name': 'Stock Only', 'login': 'rs_stock_only',
            'group_ids': [(4, self.env.ref('stock.group_stock_user').id)],
        })
        lot = self.retained_sample().lot_id
        lot.with_user(stock_user).read(['retention_sample_count', 'show_retain_sample'])
        self.location.with_user(stock_user).read(['pharma_is_retention_location'])
        for model, record in (('stock.lot', lot), ('stock.location', self.location)):
            views = self.env[model].with_user(stock_user).get_views([(False, 'form')])
            arch = etree.fromstring(views['views']['form']['arch'])
            fnames = {node.get('name') for node in arch.iter('field')}
            self.assertNotIn('retention_sample_count', fnames)
            record.with_user(stock_user).read(list(fnames & set(record._fields)))
