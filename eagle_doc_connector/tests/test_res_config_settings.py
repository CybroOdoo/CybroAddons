# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from unittest.mock import patch

from odoo.tests import tagged

from .common import EagleDocCommon, get_param


@tagged('post_install', '-at_install')
class TestResConfigSettings(EagleDocCommon):
    """Tests for res config settings."""

    def test_settings_persist_parameters(self):
        """Settings persist parameters."""
        settings = self.env['res.config.settings'].create({
            'eagle_doc_api_key': 'abc',
            'eagle_doc_base_url': 'https://x.test',
            'is_eagle_doc_auto_create_product': True,
        })
        settings.execute()
        self.assertEqual(get_param(self.env, 'eagle_doc.api_key'), 'abc')
        self.assertEqual(get_param(self.env, 'eagle_doc.base_url'), 'https://x.test')
        self.assertTrue(self.company.is_eagle_doc_auto_create_product)

    def test_check_usage_action(self):
        """Check usage action."""
        settings = self.env['res.config.settings'].create({})
        with patch.object(
                type(self.env['eagle.doc.usage.wizard']),
                '_open_usage_wizard', return_value={'type': 'x'}) as opened:
            self.assertEqual(settings.action_eagle_doc_check_usage(), {'type': 'x'})
            opened.assert_called_once()
