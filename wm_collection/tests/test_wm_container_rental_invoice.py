from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestWmContainerRentalInvoice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Container Customer',
        })
        cls.container_type = cls.env['wm.container.type'].create({
            'name': '660L Wheelie Bin',
            'code': 'WB660',
            'capacity_volume': 660.0,
        })
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Customer Site A',
            'partner_id': cls.partner.id,
        })

    def _ensure_sale_journal(self):
        """A database without an accounting chart has neither a sales journal
        nor income and receivable accounts: create them so the invoices of these tests do
        not depend on the installed data."""
        company = self.env.company
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Sales', 'code': 'TSAL', 'type': 'sale', 'company_id': company.id})
        if not journal.default_account_id:
            journal.default_account_id = self.env['account.account'].create({
                'name': 'Test Container Rental Income',
                'code': 'TCRI01',
                'account_type': 'income',
                'company_ids': [(6, 0, company.ids)],
            })
        if not self.partner.property_account_receivable_id:
            self.partner.property_account_receivable_id = self.env['account.account'].create({
                'name': 'Test Container Receivable',
                'code': 'TCRR01',
                'account_type': 'asset_receivable',
                'reconcile': True,
                'company_ids': [(6, 0, company.ids)],
            })

    def test_container_rental_invoice_creation(self):
        self._ensure_sale_journal()
        container = self.env['wm.container'].create({
            'name': 'BIN-TEST-999',
            'container_type_id': self.container_type.id,
            'collection_point_id': self.collection_point.id,
            'rental_rate': 75.0,
            'rental_period': 'monthly',
        })
        self.assertEqual(container.partner_id, self.partner)
        self.assertEqual(container.invoice_count, 0)

        # Create rental invoice
        action = container.action_create_rental_invoice()
        self.assertEqual(container.invoice_count, 1)

        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 75.0)

    def test_container_daily_rental_invoice(self):
        self._ensure_sale_journal()
        container = self.env['wm.container'].create({
            'name': 'BIN-TEST-DAILY',
            'container_type_id': self.container_type.id,
            'collection_point_id': self.collection_point.id,
            'rental_rate': 10.0,
            'rental_period': 'daily',
        })
        action = container.action_create_rental_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 10.0)
        self.assertEqual(invoice.invoice_line_ids[0].quantity, 1.0)

    def test_container_rental_invoice_unassigned_raises_error(self):
        container = self.env['wm.container'].create({
            'name': 'BIN-TEST-YARD',
            'container_type_id': self.container_type.id,
            'status': 'in_yard',
        })
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()
