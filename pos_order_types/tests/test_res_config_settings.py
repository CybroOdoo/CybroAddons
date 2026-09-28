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

class TestResConfigSettings(TransactionCase):
    """Test cases for ResConfigSettings._onchange_pos_is_order_type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


        cls.pos_config = cls.env['pos.config'].search([], limit=1)

        if not cls.pos_config:

            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config'
            })

        cls.order_type1 = cls.env['pos.order.type'].create({
            'name': 'Dine In'
        })

        cls.order_type2 = cls.env['pos.order.type'].create({
            'name': 'Takeaway'
        })


    def _new_settings(self):
        """Helper: create a fresh transient settings record."""



        return self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id
        })

    def test_onchange_clears_order_type_ids_when_disabled(self):
        """Disabling pos_is_order_type must clear pos_order_type_ids."""


        settings = self._new_settings()

        settings.pos_is_order_type = True
        settings.pos_order_type_ids = [
            (4, self.order_type1.id),
            (4, self.order_type2.id),
        ]


        settings.pos_is_order_type = False
        settings._onchange_pos_is_order_type()


        self.assertFalse(
            settings.pos_order_type_ids,
            "pos_order_type_ids should be cleared when "
            "pos_is_order_type is False."
        )

    def test_onchange_does_not_clear_when_enabled(self):
        """
        Keeping pos_is_order_type True must preserve pos_order_type_ids.
        """


        settings = self._new_settings()

        settings.pos_is_order_type = True
        settings.pos_order_type_ids = [(4, self.order_type1.id)]


        settings._onchange_pos_is_order_type()


        self.assertIn(
            self.order_type1,
            settings.pos_order_type_ids,
            "pos_order_type_ids should be preserved when "
            "pos_is_order_type is True."
        )

    def test_onchange_with_already_empty_ids_does_not_raise(self):
        """
        Calling onchange when ids are already empty should not raise errors.
        """


        settings = self._new_settings()
        settings.pos_is_order_type = False

        try:
            settings._onchange_pos_is_order_type()


        except Exception as error:

            self.fail(
                f"_onchange_pos_is_order_type raised unexpectedly: {error}"
            )

        self.assertFalse(settings.pos_order_type_ids)

    def test_onchange_returns_none(self):
        """_onchange_pos_is_order_type must return None."""


        settings = self._new_settings()
        settings.pos_is_order_type = False

        result = settings._onchange_pos_is_order_type()

        self.assertIsNone(
            result,
            "onchange_pos_is_order_type should return None."
        )
