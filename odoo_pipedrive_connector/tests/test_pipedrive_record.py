# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPipedriveRecord(TransactionCase):
    """Tests for the pipedrive.record mapping model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PipedriveRecord = cls.env['pipedrive.record']

    # ── Creation tests ──────────────────────────────────────────────────

    def test_01_create_product_record(self):
        """Create a pipedrive.record with record_type='product'."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': '100',
            'record_type': 'product',
            'odoo_ref': 1,
        })
        self.assertTrue(rec.exists())
        self.assertEqual(rec.pipedrive_reference, '100')
        self.assertEqual(rec.record_type, 'product')
        self.assertEqual(rec.odoo_ref, 1)

    def test_02_create_lead_record(self):
        """Create a pipedrive.record with record_type='lead'."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': '200',
            'record_type': 'lead',
            'odoo_ref': 2,
        })
        self.assertEqual(rec.record_type, 'lead')

    def test_03_create_partner_record(self):
        """Create a pipedrive.record with record_type='partner'."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': '300',
            'record_type': 'partner',
            'odoo_ref': 3,
        })
        self.assertEqual(rec.record_type, 'partner')

    def test_04_create_categ_record(self):
        """Create a pipedrive.record with record_type='categ'."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': '400',
            'record_type': 'categ',
            'odoo_ref': 4,
        })
        self.assertEqual(rec.record_type, 'categ')

    # ── _rec_name ───────────────────────────────────────────────────────

    def test_05_rec_name_is_pipedrive_reference(self):
        """The display name should match pipedrive_reference."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': 'REF-DISPLAY',
            'record_type': 'product',
            'odoo_ref': 10,
        })
        self.assertEqual(rec.display_name, 'REF-DISPLAY')

    # ── Write / Unlink ──────────────────────────────────────────────────

    def test_06_write_pipedrive_reference(self):
        """Update pipedrive_reference on an existing record."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': 'OLD',
            'record_type': 'product',
            'odoo_ref': 5,
        })
        rec.write({'pipedrive_reference': 'NEW'})
        self.assertEqual(rec.pipedrive_reference, 'NEW')

    def test_07_unlink_record(self):
        """Delete a pipedrive.record."""
        rec = self.PipedriveRecord.create({
            'pipedrive_reference': 'DEL',
            'record_type': 'lead',
            'odoo_ref': 6,
        })
        rec_id = rec.id
        rec.unlink()
        self.assertFalse(self.PipedriveRecord.browse(rec_id).exists())

    # ── Search / Domain ─────────────────────────────────────────────────

    def test_08_search_by_type_and_reference(self):
        """Search by record_type + pipedrive_reference returns the correct record."""
        self.PipedriveRecord.create({
            'pipedrive_reference': 'SEARCH-ME',
            'record_type': 'partner',
            'odoo_ref': 7,
        })
        found = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'SEARCH-ME'),
            ('record_type', '=', 'partner'),
        ])
        self.assertEqual(len(found), 1)
        self.assertEqual(found.odoo_ref, 7)

    def test_09_search_by_odoo_ref(self):
        """Search by odoo_ref returns the correct record."""
        self.PipedriveRecord.create({
            'pipedrive_reference': 'REF-9',
            'record_type': 'categ',
            'odoo_ref': 999,
        })
        found = self.PipedriveRecord.search([
            ('record_type', '=', 'categ'),
            ('odoo_ref', '=', 999),
        ])
        self.assertEqual(len(found), 1)

    def test_10_duplicate_references_allowed(self):
        """Two records with different types but same pipedrive_reference
        should both exist."""
        self.PipedriveRecord.create({
            'pipedrive_reference': 'SAME',
            'record_type': 'product',
            'odoo_ref': 11,
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'SAME',
            'record_type': 'partner',
            'odoo_ref': 12,
        })
        recs = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'SAME'),
        ])
        self.assertEqual(len(recs), 2)
