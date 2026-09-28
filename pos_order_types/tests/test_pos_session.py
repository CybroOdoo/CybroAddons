# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo.tests.common import TransactionCase


class TestPosSession(TransactionCase):
    """Test cases for PosSession._load_pos_data_models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


        cls.pos_config = cls.env['pos.config'].search([], limit=1)

        if not cls.pos_config:

            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config'
            })


    def test_load_pos_data_models_returns_list(self):
        """_load_pos_data_models should return a list."""


        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id
        )


        self.assertIsInstance(
            result,
            list,
            "_load_pos_data_models must return a list."
        )

    def test_load_pos_data_models_includes_pos_order_type(self):
        """'pos.order.type' must be present in the returned model list."""


        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id
        )


        self.assertIn(
            'pos.order.type',
            result,
            "'pos.order.type' should be appended to the data models list."
        )

    def test_load_pos_data_models_pos_order_type_appended_once(self):
        """'pos.order.type' should appear exactly once."""

        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id
        )

        count = result.count('pos.order.type')


        self.assertEqual(
            count,
            1,
            "'pos.order.type' should be appended exactly once."
        )

    def test_load_pos_data_models_preserves_parent_models(self):
        """Parent models returned by super() should still exist."""


        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config.id
        )

        other_models = [
            model for model in result
            if model != 'pos.order.type'
        ]


        self.assertTrue(
            other_models,
            "Parent model entries should not be removed."
        )
