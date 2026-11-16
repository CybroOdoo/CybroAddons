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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test the product highlights field."""

    def test_product_highlights(self):
        """The highlights are stored on the product template."""
        template = self.env['product.template'].create({
            'name': 'Voltro Product',
            'product_highlights': 'Fast\nLight',
        })
        self.assertEqual(template.product_highlights, 'Fast\nLight')

    def test_product_highlights_translatable(self):
        """The highlights can be translated."""
        field = self.env['product.template']._fields['product_highlights']
        self.assertTrue(field.translate)
