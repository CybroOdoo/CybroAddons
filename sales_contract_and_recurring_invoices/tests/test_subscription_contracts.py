# -*- coding: utf-8 -*-
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
from odoo import fields
from odoo.tests import common, tagged
from odoo.tools import date_utils


@tagged('post_install', '-at_install')
class TestSubscriptionContracts(common.TransactionCase):
    """ Comprehensive test cases for Subscription Contracts & Recurring Invoicing """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Contract Customer',
            'email': 'customer@example.com',
        })
        cls.other_partner = cls.env['res.partner'].create({
            'name': 'Other Customer',
        })

        cls.tax_sale_10 = cls.env['account.tax'].create({
            'name': 'Test Tax 10%',
            'type_tax_use': 'sale',
            'amount': 10.0,
            'company_id': cls.env.company.id,
        })

        cls.product_service = cls.env['product.product'].create({
            'name': 'Monthly Cloud Hosting',
            'type': 'service',
            'lst_price': 100.0,
            'taxes_id': [fields.Command.set(cls.tax_sale_10.ids)],
        })

        cls.product_addon = cls.env['product.product'].create({
            'name': 'Maintenance Support',
            'type': 'service',
            'lst_price': 50.0,
        })

    def test_01_contract_creation_and_computes(self):
        """ Test calculation of next invoice date, duration end dates, and line amounts """
        today = fields.Date.today()
        contract = self.env['subscription.contracts'].create({
            'name': 'Cloud Hosting Contract 2026',
            'partner_id': self.partner.id,
            'date_start': today,
            'recurring_invoice': 30,
            'recurring_period': 12,
            'recurring_period_interval': 'months',
            'contract_reminder': 15,
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 2.0,
                    'price_unit': 100.0,
                    'discount': 10.0,
                    'tax_ids': [fields.Command.set(self.tax_sale_10.ids)],
                }),
                fields.Command.create({
                    'product_id': self.product_addon.id,
                    'qty_ordered': 1.0,
                    'price_unit': 50.0,
                    'discount': 0.0,
                }),
            ],
        })

        # Test next invoice date calculation
        expected_next_inv = date_utils.add(today, days=30)
        self.assertEqual(contract.next_invoice_date, expected_next_inv)

        # Test end date calculation for 'months'
        expected_end = date_utils.add(today, months=12)
        self.assertEqual(contract.date_end, expected_end)

        # Test line totals
        # Line 1: 2 * 100 * (1 - 0.10) = 180 untaxed; 10% tax = 18.0; total = 198.0
        line1 = contract.contract_line_ids.filtered(lambda line: line.product_id == self.product_service)
        self.assertAlmostEqual(line1.price_subtotal, 180.0)
        self.assertAlmostEqual(line1.price_total, 198.0)

        # Line 2: 1 * 50 = 50 untaxed; 0 tax; total = 50.0
        line2 = contract.contract_line_ids.filtered(lambda line: line.product_id == self.product_addon)
        self.assertAlmostEqual(line2.price_subtotal, 50.0)
        self.assertAlmostEqual(line2.price_total, 50.0)

        # Contract totals
        self.assertAlmostEqual(contract.amount_untaxed, 230.0)
        self.assertAlmostEqual(contract.amount_tax, 18.0)
        self.assertAlmostEqual(contract.amount_total, 248.0)

        # Test report base filename
        self.assertEqual(contract._get_report_base_filename(), "Subscription Contract - Cloud Hosting Contract 2026")

        # Test interval computations for days, weeks, years
        contract.write({'recurring_period_interval': 'days', 'recurring_period': 45})
        self.assertEqual(contract.date_end, date_utils.add(today, days=45))

        contract.write({'recurring_period_interval': 'weeks', 'recurring_period': 4})
        self.assertEqual(contract.date_end, date_utils.add(today, weeks=4))

        contract.write({'recurring_period_interval': 'years', 'recurring_period': 2})
        self.assertEqual(contract.date_end, date_utils.add(today, years=2))

    def test_02_contract_line_onchanges_and_computes(self):
        """ Test unit price, uom, description, and tax fetching on contract lines """
        contract = self.env['subscription.contracts'].create({
            'name': 'Onchange Test Contract',
            'partner_id': self.partner.id,
        })
        line = self.env['subscription.contracts.line'].create({
            'subscription_contract_id': contract.id,
            'product_id': self.product_service.id,
        })
        line._compute_product_uom()
        self.assertEqual(line.product_uom_id, self.product_service.uom_id)

        line._compute_price_unit()
        self.assertEqual(line.price_unit, self.product_service.lst_price)

        line._compute_description()
        self.assertTrue(line.description)

        line._onchange_product_id_taxes()
        self.assertIn(self.tax_sale_10.id, line.tax_ids.ids)

    def test_03_contract_workflow_and_locking(self):
        """ Test state transitions: confirm, lock, unlock, cancel """
        contract = self.env['subscription.contracts'].create({
            'name': 'Lifecycle Contract',
            'partner_id': self.partner.id,
        })
        self.assertEqual(contract.state, 'new')
        self.assertFalse(contract.lock)

        # Confirm
        contract.action_to_confirm()
        self.assertEqual(contract.state, 'ongoing')

        # Lock
        contract.action_lock()
        self.assertTrue(contract.lock)

        # Unlock
        contract.action_to_unlock()
        self.assertFalse(contract.lock)

        # Cancel
        contract.action_to_cancel()
        self.assertEqual(contract.state, 'cancelled')

    def test_04_manual_invoicing_and_smart_button(self):
        """ Test manual invoice generation and invoice smart button reactivity """
        contract = self.env['subscription.contracts'].create({
            'name': 'Billing Contract',
            'partner_id': self.partner.id,
            'recurring_invoice': 30,
            'state': 'ongoing',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                    'price_unit': 100.0,
                    'discount': 5.0,
                    'tax_ids': [fields.Command.set(self.tax_sale_10.ids)],
                }),
            ],
        })

        self.assertEqual(contract.invoice_count, 0)
        self.assertFalse(contract.invoices_active)

        # Trigger manual invoice generation
        res = contract.action_generate_invoice()
        self.assertEqual(res.get('res_model'), 'account.move')
        created_invoice_id = res.get('res_id')
        invoice = self.env['account.move'].browse(created_invoice_id)

        self.assertTrue(invoice.exists())
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.contract_origin_id, contract)

        inv_line = invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.product_service)
        self.assertTrue(inv_line)
        self.assertEqual(inv_line.quantity, 1.0)
        self.assertEqual(inv_line.price_unit, 100.0)
        self.assertEqual(inv_line.discount, 5.0)

        # Verify smart button reactivity
        self.assertEqual(contract.invoice_count, 1)
        self.assertTrue(contract.invoices_active)

        # Verify invoice view action
        act = contract.action_get_invoice()
        self.assertEqual(act.get('res_model'), 'account.move')
        self.assertEqual(act.get('domain'), [('contract_origin_id', '=', contract.id)])

    def test_05_sale_order_line_linking(self):
        """ Test automatic association of sales order lines with active subscription contracts """
        today = fields.Date.today()
        contract = self.env['subscription.contracts'].create({
            'name': 'Linked Sales Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-10),
            'recurring_period': 60,
            'recurring_period_interval': 'days',
            'state': 'ongoing',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                }),
            ],
        })

        # Create sales order for same partner and product within contract duration
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'date_order': today,
            'order_line': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'product_uom_qty': 3.0,
                }),
                fields.Command.create({
                    'product_id': self.product_addon.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })

        service_line = order.order_line.filtered(lambda line: line.product_id == self.product_service)
        addon_line = order.order_line.filtered(lambda line: line.product_id == self.product_addon)

        # Service line should link to contract
        self.assertEqual(service_line.contract_id, contract)
        self.assertIn(service_line, contract.sale_order_line_ids)

        # Addon line is not covered by the contract line products
        self.assertFalse(addon_line.contract_id)

    def test_06_cron_automated_state_changes_and_recurring_billing(self):
        """ Test scheduled action for reminder warnings, expiration, and recurring invoicing """
        today = fields.Date.today()

        # Contract 1: Approaching expiration (within reminder window)
        contract_expiring = self.env['subscription.contracts'].create({
            'name': 'Expiring Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-50),
            'date_end': date_utils.add(today, days=3),
            'contract_reminder': 7,
            'state': 'ongoing',
        })

        # Contract 2: Already past end date
        contract_expired = self.env['subscription.contracts'].create({
            'name': 'Expired Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-60),
            'date_end': date_utils.add(today, days=-2),
            'contract_reminder': 5,
            'state': 'ongoing',
        })

        # Contract 3: Due for invoicing (including handling past due/missed run)
        contract_due = self.env['subscription.contracts'].create({
            'name': 'Invoicing Due Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-35),
            'date_end': date_utils.add(today, days=30),
            'recurring_invoice': 30,
            'next_invoice_date': date_utils.add(today, days=-1),  # Simulated missed run
            'state': 'ongoing',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                    'price_unit': 120.0,
                }),
            ],
        })

        # Contract 4: Cancelled contract due date should not be invoiced
        contract_cancelled = self.env['subscription.contracts'].create({
            'name': 'Cancelled Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-30),
            'date_end': date_utils.add(today, days=30),
            'next_invoice_date': today,
            'state': 'cancelled',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                }),
            ],
        })

        # Contract 5: Unconfirmed contract in 'new' state with due dates
        contract_new = self.env['subscription.contracts'].create({
            'name': 'New Draft Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-30),
            'date_end': date_utils.add(today, days=-1),
            'next_invoice_date': today,
            'state': 'new',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                }),
            ],
        })

        # Contract 6: Open-ended contract (no end date) due for invoicing
        contract_open_ended = self.env['subscription.contracts'].create({
            'name': 'Open Ended Contract',
            'partner_id': self.partner.id,
            'date_start': date_utils.add(today, days=-30),
            'date_end': False,
            'recurring_invoice': 30,
            'next_invoice_date': today,
            'state': 'ongoing',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                    'price_unit': 80.0,
                }),
            ],
        })

        # Execute scheduled action
        self.env['subscription.contracts'].subscription_contract_state_change()

        # Verify automated state transitions
        self.assertEqual(contract_expiring.state, 'expire_soon')
        self.assertEqual(contract_expired.state, 'expired')

        # Verify recurring invoice created for due contract
        self.assertEqual(contract_due.invoice_count, 1)
        invoice = contract_due.invoice_ids
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.invoice_date, today)
        self.assertTrue(contract_due.next_invoice_date > today)

        # Cancelled contract should have no invoice generated
        self.assertEqual(contract_cancelled.invoice_count, 0)

        # Unconfirmed new contract remains untouched by cron
        self.assertEqual(contract_new.state, 'new')
        self.assertEqual(contract_new.invoice_count, 0)

        # Open-ended contract is invoiced and schedule advances
        self.assertEqual(contract_open_ended.state, 'ongoing')
        self.assertEqual(contract_open_ended.invoice_count, 1)
        self.assertTrue(contract_open_ended.next_invoice_date > today)

    def test_07_pdf_report_rendering(self):
        """ Test QWeb PDF subscription contract report rendering """
        contract = self.env['subscription.contracts'].create({
            'name': 'Report Test Contract',
            'partner_id': self.partner.id,
            'recurring_period': 1,
            'recurring_period_interval': 'months',
            'contract_line_ids': [
                fields.Command.create({
                    'product_id': self.product_service.id,
                    'qty_ordered': 1.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'sales_contract_and_recurring_invoices.action_report_subscription_contracts',
            contract.ids,
        )
        self.assertTrue(pdf_content)
        self.assertTrue(len(pdf_content) > 0)

    def test_08_next_invoice_date_preservation(self):
        """ Test next_invoice_date is preserved on active contracts when dependencies change """
        today = fields.Date.today()
        contract = self.env['subscription.contracts'].create({
            'name': 'Schedule Preservation Contract',
            'partner_id': self.partner.id,
            'date_start': today,
            'recurring_invoice': 30,
            'recurring_period': 12,
            'recurring_period_interval': 'months',
            'state': 'new',
        })
        initial_next_inv = date_utils.add(today, days=30)
        self.assertEqual(contract.next_invoice_date, initial_next_inv)

        # Confirm contract
        contract.action_to_confirm()
        self.assertEqual(contract.state, 'ongoing')

        # Simulate schedule advancement (manual edit allowed because readonly=False)
        future_date = date_utils.add(today, days=60)
        contract.write({'next_invoice_date': future_date})
        self.assertEqual(contract.next_invoice_date, future_date)

        # Editing recurring_invoice or date_start should not reset next_invoice_date
        contract.write({
            'recurring_invoice': 15,
            'date_start': date_utils.add(today, days=-10),
        })
        self.assertEqual(contract.next_invoice_date, future_date)

