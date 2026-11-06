#############################################################################
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
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import HelpdeskCommon
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestHelpdeskInvoice(AccountTestInvoicingCommon, HelpdeskCommon):
    """Invoice the hours spent on the tasks of a ticket"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env['product.product'].create({
            'name': 'Support Hour',
            'type': 'service',
            'list_price': 40.0,
        })
        cls.employee_record = cls.env['hr.employee'].sudo().create(
            {'name': 'Support Agent'})

    def _log_hours(self, task, hours):
        """Timesheet on the task"""
        self.env['account.analytic.line'].sudo().create({
            'name': 'Work',
            'project_id': task.project_id.id,
            'task_id': task.id,
            'employee_id': self.employee_record.id,
            'unit_amount': hours,
        })

    def test_01_invoice_hours(self):
        """The hours of the tasks are invoiced once"""
        ticket = self._create_ticket(team_id=self.team.id,
                                     billable=True).sudo()
        with self.assertRaises(UserError):
            ticket.action_create_invoice()
        ticket.service_product_id = self.service
        task = self.env['project.task'].browse(
            ticket.action_create_tasks()['res_id'])
        with self.assertRaises(UserError):
            ticket.action_create_invoice()
        self._log_hours(task, 3)
        action = ticket.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.partner_id, self.customer)
        self.assertEqual(invoice.ticket_id, ticket)
        self.assertEqual(invoice.invoice_line_ids.quantity, 3)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 40.0)
        self.assertEqual(ticket.invoice_ids, invoice)
        self.assertTrue(task.ticket_billed)
        with self.assertRaises(UserError):
            ticket.action_create_invoice()
        # The cost of the ticket replaces the price of the product
        ticket.cost = 55.0
        second_task = self.env['project.task'].browse(
            ticket.action_create_tasks()['res_id'])
        self._log_hours(second_task, 2)
        invoice = self.env['account.move'].browse(
            ticket.action_create_invoice()['res_id'])
        self.assertEqual(invoice.invoice_line_ids.price_unit, 55.0)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2)

    def test_02_invoice_needs_customer(self):
        """A ticket without customer cannot be invoiced"""
        ticket = self._create_ticket(customer_id=False,
                                     service_product_id=self.service.id)
        with self.assertRaises(UserError):
            ticket.action_create_invoice()
