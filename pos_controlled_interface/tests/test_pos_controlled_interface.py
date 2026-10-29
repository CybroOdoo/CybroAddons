# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosControlledInterface(TransactionCase):
    """Test suite for pos_controlled_interface module covering pos.config
    and res.config.settings extensions.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.bank_journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'bank'),
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'POS Test Bank Journal',
                'type': 'bank',
                'code': 'PTB',
                'company_id': cls.company.id,
            })
        cls.payment_method = cls.env['pos.payment.method'].search([
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.payment_method:
            cls.payment_method = cls.env['pos.payment.method'].create({
                'name': 'POS Test Payment Method',
                'type': 'bank',
                'journal_id': cls.bank_journal.id,
                'company_id': cls.company.id,
            })
        # Create standard test POS configuration
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Controlled POS Shop',
            'company_id': cls.company.id,
            'payment_method_ids': [(6, 0, cls.payment_method.ids)],
        })

    def test_pos_config_default_values(self):
        """Test default values of control_discount field on pos.config."""
        new_config = self.env['pos.config'].create({
            'name': 'New Shop Defaults',
            'company_id': self.company.id,
            'payment_method_ids': [(6, 0, self.payment_method.ids)],
        })
        self.assertFalse(
            new_config.control_discount,
            "control_discount should default to False on new pos.config."
        )

    def test_pos_config_set_control_discount(self):
        """Test toggling control_discount on pos.config directly."""
        self.pos_config.write({'control_discount': True})
        self.assertTrue(
            self.pos_config.control_discount,
            "control_discount should be True after enabling."
        )
        self.pos_config.write({'control_discount': False})
        self.assertFalse(
            self.pos_config.control_discount,
            "control_discount should be False after disabling."
        )

    def test_res_config_settings_get_values(self):
        """Test that res.config.settings properly reads related values from pos_config_id."""
        self.pos_config.write({
            'control_discount': True,
        })
        settings = self.env['res.config.settings'].new({
            'pos_config_id': self.pos_config.id,
        })
        self.assertTrue(
            settings.control_discount,
            "res.config.settings should reflect control_discount=True from pos.config."
        )

    def test_res_config_settings_set_values(self):
        """Test that modifying related fields via res.config.settings writes to pos.config."""
        self.pos_config.write({
            'control_discount': False,
        })
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'control_discount': True,
        })
        settings.execute()
        self.assertTrue(
            self.pos_config.control_discount,
            "pos.config control_discount should be True after saving settings."
        )

    def test_res_config_settings_toggle_off(self):
        """Test disabling controls via res.config.settings."""
        self.pos_config.write({
            'control_discount': True,
        })
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'control_discount': False,
        })
        settings.execute()
        self.assertFalse(
            self.pos_config.control_discount,
            "pos.config control_discount should be False after disabling via settings."
        )

    def test_multiple_pos_configs_isolation(self):
        """Test that setting controls on one pos.config does not affect another."""
        config_a = self.env['pos.config'].create({
            'name': 'POS Config A',
            'company_id': self.company.id,
            'control_discount': True,
            'payment_method_ids': [(6, 0, self.payment_method.ids)],
        })
        config_b = self.env['pos.config'].create({
            'name': 'POS Config B',
            'company_id': self.company.id,
            'control_discount': False,
            'payment_method_ids': [(6, 0, self.payment_method.ids)],
        })
        self.assertTrue(config_a.control_discount)
        self.assertFalse(config_b.control_discount)

    def test_pos_config_read_fields(self):
        """Test reading control fields from pos.config as performed during POS data loading."""
        self.pos_config.write({
            'control_discount': True,
        })
        data = self.pos_config.read(['control_discount', 'name'], load=False)
        self.assertTrue(data, "Read result should not be empty.")
        record_data = data[0]
        self.assertEqual(record_data.get('control_discount'), True)

    def test_res_config_settings_view_architecture(self):
        """Test that the res.config.settings inherited view renders and contains the fields."""
        view = self.env.ref('pos_controlled_interface.res_config_settings_view_form')
        self.assertTrue(view.exists(), "Inherited settings view should exist.")
        self.assertTrue(view.active, "View should be active.")
        view_arch = self.env['res.config.settings'].get_view(view.id, 'form')
        self.assertIn('pos_control_interface', view_arch['arch'])
        self.assertIn('control_discount', view_arch['arch'])

    def test_pos_config_copy(self):
        """Test that duplicating a pos.config preserves the control fields."""
        self.pos_config.write({
            'control_discount': True,
        })
        copied_config = self.pos_config.copy({'name': 'Copied Config'})
        self.assertTrue(copied_config.control_discount)

    def test_pos_session_with_controlled_config(self):
        """Test creating a POS session with a controlled pos.config."""
        self.pos_config.write({
            'control_discount': True,
        })
        session = self.env['pos.session'].create({
            'user_id': self.env.uid,
            'config_id': self.pos_config.id,
        })
        self.assertTrue(session.exists())
        self.assertTrue(session.config_id.control_discount)
