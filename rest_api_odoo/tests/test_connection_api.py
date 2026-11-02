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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test cases for connection.api model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestConnectionApi(TransactionCase):
    """Test cases for connection.api model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1
        )
        cls.company_model = cls.env['ir.model'].search(
            [('model', '=', 'res.company')], limit=1
        )

    def test_01_create_connection_api_defaults(self):
        """Test creating a connection.api record with default boolean values."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
        })
        self.assertTrue(conn.id, "Connection API record should be created.")
        self.assertEqual(conn.model_id, self.partner_model)
        self.assertFalse(conn.is_get, "Default is_get should be False.")
        self.assertFalse(conn.is_post, "Default is_post should be False.")
        self.assertFalse(conn.is_put, "Default is_put should be False.")
        self.assertFalse(conn.is_delete, "Default is_delete should be False.")

    def test_02_create_connection_api_with_flags(self):
        """Test creating a connection.api record with all HTTP method flags enabled."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
            'is_post': True,
            'is_put': True,
            'is_delete': True,
        })
        self.assertTrue(conn.is_get, "is_get should be True.")
        self.assertTrue(conn.is_post, "is_post should be True.")
        self.assertTrue(conn.is_put, "is_put should be True.")
        self.assertTrue(conn.is_delete, "is_delete should be True.")

    def test_03_rec_name_display_name(self):
        """Test that rec_name / display_name reflects the related model."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
        })
        self.assertEqual(
            conn._rec_name,
            'model_id',
            "_rec_name must be 'model_id'."
        )
        self.assertEqual(
            conn.display_name,
            self.partner_model.display_name,
            "display_name should match the model_id display_name."
        )

    def test_04_write_flags(self):
        """Test updating HTTP method flags on an existing connection.api record."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': False,
            'is_post': False,
            'is_put': False,
            'is_delete': False,
        })
        # Enable GET and POST
        conn.write({
            'is_get': True,
            'is_post': True,
        })
        self.assertTrue(conn.is_get)
        self.assertTrue(conn.is_post)
        self.assertFalse(conn.is_put)
        self.assertFalse(conn.is_delete)

        # Update to enable PUT and DELETE, and disable GET
        conn.write({
            'is_get': False,
            'is_put': True,
            'is_delete': True,
        })
        self.assertFalse(conn.is_get)
        self.assertTrue(conn.is_post)
        self.assertTrue(conn.is_put)
        self.assertTrue(conn.is_delete)

    def test_05_unlink_connection_api(self):
        """Test deleting a connection.api record."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        conn_id = conn.id
        conn.unlink()
        searched = self.env['connection.api'].search([('id', '=', conn_id)])
        self.assertFalse(searched.exists(), "Record should no longer exist after unlink.")

    def test_06_search_and_filter(self):
        """Test searching connection.api records by model and by allowed methods."""
        conn_partner = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
            'is_post': False,
        })
        conn_company = self.env['connection.api'].create({
            'model_id': self.company_model.id,
            'is_get': False,
            'is_post': True,
        })

        search_by_model = self.env['connection.api'].search([
            ('model_id', '=', self.partner_model.id)
        ])
        self.assertIn(conn_partner, search_by_model)
        self.assertNotIn(conn_company, search_by_model)

        search_by_post = self.env['connection.api'].search([
            ('is_post', '=', True)
        ])
        self.assertIn(conn_company, search_by_post)
        self.assertNotIn(conn_partner, search_by_post)

    def test_07_copy_connection_api(self):
        """Test copying an existing connection.api record."""
        conn = self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
            'is_post': True,
            'is_put': False,
            'is_delete': True,
        })
        conn_copy = conn.copy()
        self.assertTrue(conn_copy.id)
        self.assertNotEqual(conn.id, conn_copy.id)
        self.assertEqual(conn_copy.model_id, self.partner_model)
        self.assertTrue(conn_copy.is_get)
        self.assertTrue(conn_copy.is_post)
        self.assertFalse(conn_copy.is_put)
        self.assertTrue(conn_copy.is_delete)

    def test_08_model_id_domain(self):
        """Test that model_id domain excludes transient models."""
        field_domain = self.env['connection.api']._fields['model_id'].domain
        self.assertEqual(
            field_domain,
            "[('transient', '=', False)]",
            "model_id domain should exclude transient models."
        )
