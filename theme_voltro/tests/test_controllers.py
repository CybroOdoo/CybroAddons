################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

from odoo.tests import tagged

from odoo.addons.theme_voltro.controllers.theme_voltro import (
    VoltroProductSnippets,
)
from odoo.addons.theme_voltro.controllers.website import VoltroWebsiteForm
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestVoltroProductSnippets(WebsiteSaleCommon):
    """Test the routes that fill the Voltro product snippets."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme, which loads the snippet templates."""
        super().setUpClass()
        theme = cls.env['ir.module.module'].with_user(
            cls.env.ref('base.user_admin')).search(
            [('name', '=', 'theme_voltro')], limit=1)
        theme._theme_load(cls.website)

    def test_product_arrivals(self):
        """The arrivals snippet renders a published product."""
        self.product.product_tmpl_id.sudo().website_published = True
        with MockRequest(self.env, website=self.website):
            result = VoltroProductSnippets().product_arrivals()
        self.assertIn(self.product.product_tmpl_id.name, str(result))

    def test_product_arrivals_limit(self):
        """The arrivals snippet shows at most four products."""
        self.env['product.template'].sudo().create([{
            'name': 'Voltro Arrival {}'.format(index),
            'website_published': True,
        } for index in range(6)])
        with MockRequest(self.env, website=self.website):
            result = VoltroProductSnippets().product_arrivals()
        self.assertEqual(str(result).count('splide__slide'), 4)

    def test_product_categories(self):
        """Only the root categories are rendered."""
        root = self.env['product.public.category'].sudo().create({
            'name': 'Voltro Root Category',
        })
        child = self.env['product.public.category'].sudo().create({
            'name': 'Voltro Child Category',
            'parent_id': root.id,
        })
        with MockRequest(self.env, website=self.website):
            result = str(VoltroProductSnippets().product_categories())
        self.assertIn(root.name, result)
        self.assertNotIn(child.name, result)


@tagged('post_install', '-at_install')
class TestVoltroWebsiteForm(WebsiteSaleCommon):
    """Test the merge of the first and last name of the contact form."""

    def _submit(self, model_name, params):
        """Submit the form and return the params seen by the parent method."""
        with MockRequest(self.env, website=self.website) as request:
            request.params.update(params)
            with patch.object(
                    WebsiteForm, 'website_form', return_value='done',
            ) as parent:
                result = VoltroWebsiteForm.website_form.original_endpoint(
                    VoltroWebsiteForm(), model_name)
            self.assertEqual(result, 'done')
            self.assertTrue(parent.called)
            return dict(request.params)

    def test_names_are_merged(self):
        """The first and last name become one name on a mail form."""
        params = self._submit(
            'mail.mail', {'name': 'John', 'second_name': 'Doe'})
        self.assertEqual(params['name'], 'John Doe')
        self.assertNotIn('second_name', params)

    def test_empty_last_name(self):
        """An empty last name leaves no trailing space."""
        params = self._submit('mail.mail', {'name': 'John', 'second_name': ''})
        self.assertEqual(params['name'], 'John')

    def test_name_alone_is_kept(self):
        """A form without a last name is passed on as it is."""
        params = self._submit('mail.mail', {'name': 'John'})
        self.assertEqual(params, {'name': 'John'})

    def test_other_models_are_kept(self):
        """The names of a form for another model are not merged."""
        values = {'name': 'John', 'second_name': 'Doe'}
        self.assertEqual(self._submit('res.partner', dict(values)), values)
