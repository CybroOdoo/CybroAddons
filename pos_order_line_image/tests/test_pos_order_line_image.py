# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import logging
from lxml import etree
from odoo.tests import tagged
from odoo.tools import file_open
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestPosOrderLineImage(TestPointOfSaleHttpCommon):
    """Test suite for pos_order_line_image module:
    Verifies that product images are displayed in order lines on the POS screen.
    """

    _test_user_groups = None

    def test_pos_order_line_image_xml_extension(self):
        """Test that the XML template correctly inherits OrderSummary and sets showImage to true."""
        with file_open('pos_order_line_image/static/src/xml/pos_order_line.xml', 'rb') as f:
            xml_content = f.read()
        tree = etree.fromstring(xml_content)

        # Verify template inheritance
        templates = tree.xpath("//t[@t-name='pos_order_line_image.OrderSummary']")
        self.assertTrue(templates, "Template pos_order_line_image.OrderSummary should exist.")
        template = templates[0]
        self.assertEqual(template.get('t-inherit'), 'point_of_sale.OrderSummary')
        self.assertEqual(template.get('t-inherit-mode'), 'extension')

        # Verify xpath attributes modification
        xpaths = template.xpath(".//xpath[@expr='//Orderline']")
        self.assertTrue(xpaths, "XPath targeting //Orderline must be present.")
        xpath = xpaths[0]
        self.assertEqual(xpath.get('position'), 'attributes')

        attribute_nodes = xpath.xpath("./attribute[@name='showImage']")
        self.assertTrue(attribute_nodes, "attribute name='showImage' must be defined.")
        self.assertEqual(attribute_nodes[0].text.strip(), 'true', "showImage must be set to 'true'.")

    def test_pos_order_line_image_tour(self):
        """Start the tour to test that the product image is displayed in the order line on the POS screen."""
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour('pos_order_line_image_tour')
