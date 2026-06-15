# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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

from odoo.tests import common
from odoo import fields
from datetime import timedelta
from unittest.mock import patch


class TestDueDateReminder(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDueDateReminder, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'invoice_policy': 'order',
        })

        # Configure settings
        settings = cls.env['res.config.settings'].create({
            'reminder_sales': True,
            'set_date_sales': 2,
            'reminder_invoicing': True,
            'set_date_invoicing': 3,
        })
        settings.execute()

    def test_01_invoice_due_date_reminder(self):
        """Test invoice due date reminder mail."""
        today = fields.Date.today()
        # Set invoice due date to today + 3 days (matches set_date_invoicing = 3)
        due_date = today + timedelta(days=3)
        
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date_due': due_date,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })]
        })
        
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as mock_send_mail:
            self.env['account.move'].action_send_mail_invoice()
            mock_send_mail.assert_called()

        # Test posted invoice
        move.action_post()
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as mock_send_mail:
            self.env['account.move'].action_send_mail_invoice()
            mock_send_mail.assert_called()

    def test_02_sale_order_due_date_reminder(self):
        """Test sale order due date reminder mail."""
        today = fields.Date.today()
        # Set sale order due date to today + 2 days (matches set_date_sales = 2)
        due_date = today + timedelta(days=2)
        
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'due_date_order': due_date,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })]
        })
        sale_order.action_confirm()
        
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as mock_send_mail:
            self.env['sale.order'].action_send_mail_sale_order()
            mock_send_mail.assert_called()
