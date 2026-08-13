# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Prasudhi A(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
from unittest.mock import patch, MagicMock
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'product_image_suggestion')
class TestProductTemplate(TransactionCase):
    """Test cases for the ProductTemplate extension provided by the
    product_image_suggestion module."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.template'].create({
            'name': 'Test Product For Image Search',
        })
        # Minimal valid PNG (1×1 pixel) for use as a mock download result
        self.png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

    # ------------------------------------------------------------------
    # Field defaults
    # ------------------------------------------------------------------

    def test_default_image_limit(self):
        """image_limit should default to 5 on a newly created product."""
        self.assertEqual(
            self.product.image_limit, 5,
            "Default image_limit should be 5."
        )

    def test_default_resize_image(self):
        """resize_image should default to True on a newly created product."""
        self.assertTrue(
            self.product.resize_image,
            "Default resize_image should be True."
        )

    def test_default_search_field_empty(self):
        """search_field should be empty/False by default."""
        self.assertFalse(
            self.product.search_field,
            "search_field should be empty by default."
        )

    # ------------------------------------------------------------------
    # _onchange_image_limit
    # ------------------------------------------------------------------

    def test_onchange_image_limit_above_10_raises(self):
        """_onchange_image_limit() must raise UserError when limit > 10."""
        self.product.image_limit = 15
        with self.assertRaises(UserError,
                               msg="UserError expected when image_limit > 10"):
            self.product._onchange_image_limit()

    def test_onchange_image_limit_exactly_10_no_error(self):
        """_onchange_image_limit() should NOT raise when limit == 10."""
        self.product.image_limit = 10
        try:
            self.product._onchange_image_limit()
        except UserError:
            self.fail("_onchange_image_limit() raised UserError unexpectedly "
                      "when limit == 10.")

    def test_onchange_image_limit_below_10_no_error(self):
        """_onchange_image_limit() should NOT raise when limit < 10."""
        self.product.image_limit = 3
        try:
            self.product._onchange_image_limit()
        except UserError:
            self.fail("_onchange_image_limit() raised UserError unexpectedly "
                      "when limit == 3.")

    # ------------------------------------------------------------------
    # action_search_image – error paths
    # ------------------------------------------------------------------

    def test_action_search_image_no_search_field_raises(self):
        """action_search_image() should raise UserError when search_field is
        empty (AttributeError on None.replace triggers the user-facing error)."""
        self.product.search_field = False
        with self.assertRaises(UserError,
                               msg="UserError expected when search_field is "
                                   "empty"):
            self.product.action_search_image()

    def test_action_search_image_no_results_raises(self):
        """action_search_image() should raise UserError('No image suggestions
        …') when the downloader returns an empty collection."""
        self.product.search_field = 'laptop'
        self.product.image_limit = 2

        with patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.downloader.download',
            return_value=set()
        ):
            with self.assertRaises(UserError) as ctx:
                self.product.action_search_image()
        self.assertIn('No image suggestions',
                      str(ctx.exception.args[0]),
                      "UserError message should mention 'No image suggestions'.")

    # ------------------------------------------------------------------
    # action_search_image – happy path (mocked network)
    # ------------------------------------------------------------------

    def test_action_search_image_clears_existing_suggestions(self):
        """action_search_image() should remove existing search_image_ids
        before adding new ones."""
        # Pre-seed an existing suggestion
        self.env['product.image.suggestion'].create({
            'image': base64.b64encode(self.png_bytes),
            'product_tmpl_id': self.product.id,
        })
        self.product.search_field = 'chair'
        self.product.image_limit = 1
        self.product.resize_image = False

        mock_response = MagicMock()
        mock_response.content = self.png_bytes

        with patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.downloader.download',
            return_value={'https://example.com/chair.jpg'}
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.requests.get',
            return_value=mock_response
        ):
            self.product.action_search_image()

        remaining = self.env['product.image.suggestion'].search(
            [('product_tmpl_id', '=', self.product.id)]
        )
        # Only the newly created suggestion from this run should exist
        self.assertEqual(len(remaining), 1,
                         "Old suggestions should be cleared; only 1 new "
                         "suggestion expected.")

    def test_action_search_image_creates_suggestions_no_resize(self):
        """action_search_image() should create product.image.suggestion
        records when the downloader returns URLs and resize_image is False."""
        self.product.search_field = 'keyboard'
        self.product.image_limit = 2
        self.product.resize_image = False

        mock_response = MagicMock()
        mock_response.content = self.png_bytes

        fake_urls = {
            'https://example.com/img1.jpg',
            'https://example.com/img2.jpg',
        }

        with patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.downloader.download',
            return_value=fake_urls
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.requests.get',
            return_value=mock_response
        ):
            self.product.action_search_image()

        suggestions = self.env['product.image.suggestion'].search(
            [('product_tmpl_id', '=', self.product.id)]
        )
        self.assertEqual(
            len(suggestions), len(fake_urls),
            "One product.image.suggestion record should be created per URL "
            "returned by the downloader."
        )

    def test_action_search_image_creates_suggestions_with_resize(self):
        """action_search_image() should invoke the PIL resize pipeline and
        attempt to create a product.image.suggestion record when resize_image
        is True.  We mock the ORM create() call to avoid Odoo's ir.attachment
        image-validation pipeline (which would reject mocked bytes)."""
        self.product.search_field = 'monitor'
        self.product.image_limit = 1
        self.product.resize_image = True

        mock_response = MagicMock()
        mock_response.content = self.png_bytes

        mock_img = MagicMock()
        mock_img.format = 'PNG'

        created_vals = []

        def fake_suggestion_create(vals_list):
            """Capture the vals without touching ir.attachment."""
            if isinstance(vals_list, list):
                created_vals.extend(vals_list)
            else:
                created_vals.append(vals_list)
            return self.env['product.image.suggestion'].browse([])

        with patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.downloader.download',
            return_value={'https://example.com/monitor.jpg'}
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.requests.get',
            return_value=mock_response
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.Image.open',
            return_value=mock_img
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.resizeimage.resize_contain',
            return_value=mock_img
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.tempfile.mkstemp',
            return_value=(0, '/tmp/test_image.png')
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.os.remove'
        ), patch(
            'builtins.open',
            MagicMock(return_value=MagicMock(
                __enter__=lambda s, *a: s,
                __exit__=MagicMock(return_value=False),
                write=MagicMock(),
                read=MagicMock(return_value=self.png_bytes),
            ))
        ), patch.object(
            type(self.env['product.image.suggestion']),
            'create',
            side_effect=fake_suggestion_create
        ):
            self.product.action_search_image()

        self.assertEqual(len(created_vals), 1,
                         "create() should have been called once with image "
                         "vals when resize_image is True.")
        self.assertIn('image', created_vals[0],
                      "The vals passed to create() should contain an 'image' "
                      "key.")
        self.assertEqual(created_vals[0].get('product_tmpl_id'),
                         self.product.id,
                         "The vals should reference the correct product "
                         "template.")

    def test_action_search_image_query_string_formatting(self):
        """search_field spaces and commas should be replaced with underscores
        when building the download query string."""
        self.product.search_field = 'red, apple fruit'
        self.product.image_limit = 1
        self.product.resize_image = False

        mock_response = MagicMock()
        mock_response.content = self.png_bytes

        captured_query = []

        def fake_download(query, **kwargs):
            captured_query.append(query)
            return {'https://example.com/apple.jpg'}

        with patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.downloader.download',
            side_effect=fake_download
        ), patch(
            'odoo.addons.product_image_suggestion.models.'
            'product_template.requests.get',
            return_value=mock_response
        ):
            self.product.action_search_image()

        self.assertEqual(len(captured_query), 1,
                         "downloader.download should have been called once.")
        self.assertEqual(captured_query[0], 'red__apple_fruit',
                         "Spaces and commas in search_field should be "
                         "replaced with underscores in the query string.")
