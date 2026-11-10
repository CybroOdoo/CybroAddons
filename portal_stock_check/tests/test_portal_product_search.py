#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestPortalProductSearch(HttpCase):
    """Test the portal product availability page and search route."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(
            cls.env, login='portal_stock_user', password='portal_stock_user',
            groups='base.group_portal',
        )
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.product_published = cls._create_product(
            'Stock Check Chair', published=True, qty=10)
        cls.product_unpublished = cls._create_product(
            'Stock Check Hidden Chair', published=False, qty=5)
        cls.product_other = cls._create_product(
            'Stock Check Table', published=True, qty=0)

    @classmethod
    def _create_product(cls, name, published, qty):
        """Create a storable product with the given on-hand quantity."""
        template = cls.env['product.template'].create({
            'name': name,
            'type': 'consu',
            'is_storable': True,
            'is_published': published,
        })
        product = template.product_variant_id
        if qty:
            quant = cls.env['stock.quant']
            # pylint: disable-next=protected-access
            quant._update_available_quantity(
                product, cls.warehouse.lot_stock_id, qty)
        return product

    def _search(self, text):
        """Call the search route as the portal user."""
        self.authenticate('portal_stock_user', 'portal_stock_user')
        return self.make_jsonrpc_request(
            '/product/search', {'args': {'product': text}})

    def test_portal_page_renders_for_portal_user(self):
        """A logged-in portal user can open the availability page."""
        self.authenticate('portal_stock_user', 'portal_stock_user')
        response = self.url_open('/my/product-availability')
        self.assertEqual(response.status_code, 200)
        self.assertIn('product_name_input', response.text)

    def test_portal_page_requires_login(self):
        """An anonymous visitor is redirected to the login page."""
        response = self.url_open('/my/product-availability',
                                 allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/web/login', response.headers.get('Location', ''))

    def test_portal_home_shows_availability_card(self):
        """The portal home page links to the availability page."""
        self.authenticate('portal_stock_user', 'portal_stock_user')
        response = self.url_open('/my')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my/product-availability', response.text)

    def test_search_returns_matching_published_product(self):
        """The search returns the name and quantity of a product."""
        result = self._search('Stock Check Chair')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.product_published.id)
        self.assertEqual(result[0]['display_name'], 'Stock Check Chair')
        self.assertEqual(result[0]['qty_available'], 10)

    def test_search_is_case_insensitive_and_partial(self):
        """A partial, lower-case text still finds the product."""
        result = self._search('check cha')
        self.assertEqual(
            [r['id'] for r in result], [self.product_published.id])

    def test_search_excludes_unpublished_products(self):
        """Unpublished products are never exposed to the portal."""
        result = self._search('Hidden')
        self.assertEqual(result, [])

    def test_search_returns_several_matches(self):
        """Every published product matching the text is returned."""
        result = self._search('Stock Check')
        self.assertCountEqual(
            [r['id'] for r in result],
            [self.product_published.id, self.product_other.id],
        )

    def test_search_shows_zero_quantity(self):
        """A product with no stock is returned with a zero quantity."""
        result = self._search('Stock Check Table')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['qty_available'], 0)

    def test_search_without_match_returns_empty_list(self):
        """No match gives an empty list."""
        self.assertEqual(self._search('no such product xyz'), [])

    def test_search_with_empty_text_returns_empty_list(self):
        """Empty or blank text gives an empty list."""
        self.assertEqual(self._search(''), [])
        self.assertEqual(self._search('   '), [])
