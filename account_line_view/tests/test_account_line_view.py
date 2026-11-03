##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
##############################################################################
"""Unit test suite for account_line_view module."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'account_line_view')
class TestAccountLineView(TransactionCase):
    """Test cases for Account Line View module."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for account move lines and views."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Account Customer',
        })
        cls.sample_image = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z'
            '/D/PwAHAwL/qGeMxAAAAABJRU5ErkJggg=='
        )
        cls.product_with_image = cls.env['product.product'].create({
            'name': 'Product with Image',
            'image_1920': cls.sample_image,
            'list_price': 100.0,
            'standard_price': 60.0,
        })
        cls.product_no_image = cls.env['product.product'].create({
            'name': 'Product without Image',
            'image_1920': False,
            'list_price': 50.0,
            'standard_price': 30.0,
        })

    def test_product_image_field_related(self):
        """Verify product_image related field on account.move.line."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product_with_image.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': self.product_no_image.id,
                    'quantity': 2,
                    'price_unit': 50.0,
                }),
            ],
        })
        line_with_img = move.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_with_image,
        )
        line_no_img = move.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product_no_image,
        )

        self.assertTrue(line_with_img.product_image)
        self.assertEqual(
            line_with_img.product_image,
            self.product_with_image.image_1920,
        )
        self.assertFalse(line_no_img.product_image)

        # Update product image and check related reflection
        self.product_with_image.image_1920 = False
        self.assertFalse(line_with_img.product_image)

    def test_actions_definitions(self):
        """Verify window actions defined for account line views."""
        actions = [
            ('account_line_view.action_account_line_view', 'Account Line', 'Account Lines Views'),
            ('account_line_view.action_invoice_line_view', 'Invoice Line', 'Invoice Lines Views'),
            ('account_line_view.action_bill_line_view', 'Bill Line', 'Bill Lines Views'),
            ('account_line_view.action_credit_note_line_view', 'Credit Note Line', 'Credit Note Lines'),
            ('account_line_view.action_refund_line_view', 'Refund Line', 'Refund Lines Views'),
        ]
        for xml_id, expected_name, expected_help in actions:
            action = self.env.ref(xml_id)
            self.assertEqual(action.res_model, 'account.move.line')
            self.assertEqual(action.name, expected_name)
            self.assertIn('list', action.view_mode)
            self.assertIn('kanban', action.view_mode)
            self.assertIn('pivot', action.view_mode)
            self.assertIn('graph', action.view_mode)
            self.assertIn('calendar', action.view_mode)
            self.assertIn(expected_help, action.help)

    def test_views_definitions(self):
        """Verify that all views defined in XML can be retrieved and parsed."""
        view_xml_ids = [
            'account_line_view.account_line_view_list',
            'account_line_view.account_line_view_kanban',
            'account_line_view.account_line_view_pivot',
            'account_line_view.account_line_view_graph',
            'account_line_view.account_line_view_calender',
            'account_line_view.invoice_line_view_list',
            'account_line_view.invoice_line_view_kanban',
            'account_line_view.invoice_line_view_pivot',
            'account_line_view.invoice_line_view_graph',
            'account_line_view.invoice_line_view_calender',
            'account_line_view.bill_line_view_list',
            'account_line_view.bill_line_view_kanban',
            'account_line_view.bill_line_view_pivot',
            'account_line_view.bill_line_view_graph',
            'account_line_view.bill_line_view_calender',
            'account_line_view.credit_note_line_view_list',
            'account_line_view.credit_note_line_view_kanban',
            'account_line_view.credit_note_line_view_pivot',
            'account_line_view.credit_note_line_view_graph',
            'account_line_view.credit_note_line_view_calender',
            'account_line_view.refund_line_view_list',
            'account_line_view.refund_line_view_kanban',
            'account_line_view.refund_line_view_pivot',
            'account_line_view.refund_line_view_graph',
            'account_line_view.refund_line_view_calender',
            'account_line_view.view_move_line_form',
        ]
        for xml_id in view_xml_ids:
            view = self.env.ref(xml_id)
            self.assertTrue(view)
            self.assertEqual(view.model, 'account.move.line')

        # Verify graph and calendar string titles
        expected_strings = [
            ('account_line_view.account_line_view_graph', 'graph', 'Account Line'),
            ('account_line_view.invoice_line_view_graph', 'graph', 'Invoice Line'),
            ('account_line_view.bill_line_view_graph', 'graph', 'Bill Line'),
            ('account_line_view.credit_note_line_view_graph', 'graph', 'Credit Note Line'),
            ('account_line_view.refund_line_view_graph', 'graph', 'Refund Line'),
            ('account_line_view.account_line_view_calender', 'calendar', 'Account Line'),
            ('account_line_view.invoice_line_view_calender', 'calendar', 'Invoice Line'),
            ('account_line_view.bill_line_view_calender', 'calendar', 'Bill Line'),
            ('account_line_view.credit_note_line_view_calender', 'calendar', 'Credit Note Line'),
            ('account_line_view.refund_line_view_calender', 'calendar', 'Refund Line'),
        ]
        for view_xml_id, tag_name, expected_str in expected_strings:
            view = self.env.ref(view_xml_id)
            self.assertIn(f'string="{expected_str}"', view.arch)

    def test_menus_definitions(self):
        """Verify that menus exist and point to the right actions."""
        menus = [
            ('account_line_view.menu_account_line_view',
             'account_line_view.action_account_line_view'),
            ('account_line_view.menu_invoice_line_view',
             'account_line_view.action_invoice_line_view'),
            ('account_line_view.menu_bill_line_view',
             'account_line_view.action_bill_line_view'),
            ('account_line_view.menu_credit_note_line_view',
             'account_line_view.action_credit_note_line_view'),
            ('account_line_view.menu_refund_line_view',
             'account_line_view.action_refund_line_view'),
        ]
        for menu_id, action_id in menus:
            menu = self.env.ref(menu_id)
            expected_action = self.env.ref(action_id)
            self.assertEqual(menu.action, expected_action)

    def test_different_move_types_lines(self):
        """Verify invoice, bill, credit note and refund lines querying."""
        # Customer Invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_with_image.id,
                'quantity': 1,
                'price_unit': 120.0,
            })],
        })
        # Vendor Bill
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_with_image.id,
                'quantity': 2,
                'price_unit': 80.0,
            })],
        })
        # Customer Credit Note
        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_with_image.id,
                'quantity': 1,
                'price_unit': 120.0,
            })],
        })
        # Vendor Refund / Debit Note
        refund = self.env['account.move'].create({
            'move_type': 'in_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_with_image.id,
                'quantity': 1,
                'price_unit': 80.0,
            })],
        })

        # Test search domains
        inv_lines = self.env['account.move.line'].search([
            ('id', 'in', invoice.invoice_line_ids.ids),
            ('move_type', '=', 'out_invoice'),
            ('product_id', '!=', False),
        ])
        self.assertEqual(len(inv_lines), 1)

        bill_lines = self.env['account.move.line'].search([
            ('id', 'in', bill.invoice_line_ids.ids),
            ('move_type', '=', 'in_invoice'),
            ('product_id', '!=', False),
        ])
        self.assertEqual(len(bill_lines), 1)

        credit_lines = self.env['account.move.line'].search([
            ('id', 'in', credit_note.invoice_line_ids.ids),
            ('move_type', '=', 'out_refund'),
            ('product_id', '!=', False),
        ])
        self.assertEqual(len(credit_lines), 1)

        refund_lines = self.env['account.move.line'].search([
            ('id', 'in', refund.invoice_line_ids.ids),
            ('move_type', '=', 'in_refund'),
            ('product_id', '!=', False),
        ])
        self.assertEqual(len(refund_lines), 1)
