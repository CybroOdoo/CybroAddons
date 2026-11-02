###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestAccountDashboardConfig(TransactionCase):
    """Test suite for user dashboard configuration model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_model = cls.env['account.dashboard.config']
        cls.test_user = cls.env['res.users'].create({
            'name': 'Dashboard Config User',
            'login': 'dashboard_config_user@example.com',
            'email': 'dashboard_config_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_readonly').id])],
        })

    def test_get_or_create_config_new(self):
        """Test creating initial dashboard configuration for a new user."""
        config_data = self.config_model.with_user(self.test_user).get_or_create_config()
        self.assertTrue(config_data.get('id'), "Config ID should be returned")
        self.assertEqual(config_data.get('default_period'), 'this_month')
        self.assertEqual(config_data.get('amount_format'), 'full')
        self.assertEqual(config_data.get('theme'), 'dark')
        self.assertIn(self.env.company.id, config_data.get('company_ids', []))
        self.assertIsInstance(config_data.get('collapsed_widgets'), list)
        self.assertIsInstance(config_data.get('hidden_kpis'), list)
        self.assertIsInstance(config_data.get('kpi_order'), list)
        self.assertIsInstance(config_data.get('hidden_charts'), list)
        self.assertIsInstance(config_data.get('chart_order'), list)
        self.assertIsInstance(config_data.get('layout_config'), dict)

    def test_get_or_create_config_existing(self):
        """Test retrieving existing dashboard configuration without duplicating."""
        first_call = self.config_model.with_user(self.test_user).get_or_create_config()
        second_call = self.config_model.with_user(self.test_user).get_or_create_config()
        self.assertEqual(first_call['id'], second_call['id'], "Should reuse existing config record")

    def test_save_config(self):
        """Test saving and updating dashboard settings."""
        config_data = self.config_model.with_user(self.test_user).get_or_create_config()
        config_record = self.config_model.browse(config_data['id'])

        vals = {
            'default_period': 'this_quarter',
            'amount_format': 'M',
            'date_from': '2026-01-01',
            'date_to': '2026-03-31',
            'collapsed_widgets': ['widget_charts_1'],
            'hidden_kpis': ['net_profit'],
            'kpi_order': ['revenue', 'expenses'],
            'hidden_charts': ['profit_trend'],
            'chart_order': ['revenue_expense'],
            'layout_config': {'columns': 2, 'density': 'compact'},
            'theme': 'light',
            'company_ids': [self.env.company.id],
        }
        res = config_record.with_user(self.test_user).save_config(vals)
        self.assertTrue(res)

        self.assertEqual(config_record.default_period, 'this_quarter')
        self.assertEqual(config_record.amount_format, 'M')
        self.assertEqual(str(config_record.date_from), '2026-01-01')
        self.assertEqual(str(config_record.date_to), '2026-03-31')
        self.assertEqual(config_record.collapsed_widgets, ['widget_charts_1'])
        self.assertEqual(config_record.hidden_kpis, ['net_profit'])
        self.assertEqual(config_record.kpi_order, ['revenue', 'expenses'])
        self.assertEqual(config_record.hidden_charts, ['profit_trend'])
        self.assertEqual(config_record.chart_order, ['revenue_expense'])
        self.assertEqual(config_record.layout_config, {'columns': 2, 'density': 'compact'})
        self.assertEqual(config_record.theme, 'light')
        self.assertEqual(config_record.company_ids.ids, [self.env.company.id])

    def test_unique_user_constraint(self):
        """Verify that a user cannot have multiple dashboard configuration records."""
        self.config_model.create({'user_id': self.test_user.id})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.config_model.create({'user_id': self.test_user.id})
