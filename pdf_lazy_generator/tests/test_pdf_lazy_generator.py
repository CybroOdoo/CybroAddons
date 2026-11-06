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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import common
from odoo.modules.registry import Registry

class TestPdfLazyGenerator(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a partner and an invoice for testing
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        # Find a valid PDF report for account.move
        cls.report = cls.env['ir.actions.report'].search([
            ('model', '=', 'account.move'),
            ('report_type', '=', 'qweb-pdf')
        ], limit=1)

    def test_01_background_generation_logic(self):
        """Test the core logic of background PDF generation for standard reports."""
        if not self.report:
            self.skipTest("No account.move PDF report found")

        report_name = self.report.report_name
        docids = [self.invoice.id]

        # We mock Registry().cursor() to return our current cursor so the test sees our data
        # even though _generate_pdf_thread normally creates a new environment with a new cursor.
        with patch.object(Registry, 'cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value = self.env.cr
            
            # We also need to avoid commit/rollback in tests
            with patch.object(self.env.cr, 'commit'), patch.object(self.env.cr, 'rollback'):
                # Use class-level patch to avoid read-only attribute error on Odoo 18 models
                with patch.object(type(self.env['bus.bus']), '_sendone') as mock_sendone:
                    self.env['ir.actions.report']._generate_pdf_thread(
                        report_name, docids, request_id='test_request_123', tab_id='tab_1'
                    )

                    # 1. Check if attachment was created
                    attachment = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.move'),
                        ('res_id', '=', self.invoice.id),
                        ('is_background_pdf', '=', True)
                    ])
                    self.assertTrue(attachment, "Background PDF attachment should be created")
                    self.assertIn(self.invoice.name or "Invoice", attachment.name)
                    self.assertEqual(attachment.mimetype, 'application/pdf')

                    # 2. Check if bus notification was sent
                    mock_sendone.assert_called_once()
                    partner, channel, data = mock_sendone.call_args[0]
                    self.assertEqual(channel, 'pdf_download')
                    self.assertEqual(data['request_id'], 'test_request_123')
                    self.assertEqual(data['tab_id'], 'tab_1')
                    self.assertIn(f'/web/content/{attachment.id}', data['url'])

    def test_02_chatter_attachment(self):
        """Test if PDF is attached to chatter when configured."""
        if not self.report:
            self.skipTest("No account.move PDF report found")

        # Enable chatter attachment via config parameter
        self.env['ir.config_parameter'].set_param('pdf_lazy_generator.is_attach_pdf_in_chatter', 'True')

        report_name = self.report.report_name
        docids = [self.invoice.id]

        initial_msg_count = len(self.invoice.message_ids)

        # Patch commit/rollback FIRST (outermost) so when Registry.cursor returns
        # self.env.cr, any call to new_cr.commit() hits the mock, not the real
        # "forbidden" cursor method enforced by Odoo's test framework.
        with patch.object(self.env.cr, 'commit'), patch.object(self.env.cr, 'rollback'):
            with patch.object(Registry, 'cursor') as mock_cursor:
                mock_cursor.return_value.__enter__.return_value = self.env.cr
                with patch.object(type(self.env['bus.bus']), '_sendone'):
                    self.env['ir.actions.report']._generate_pdf_thread(report_name, docids)

        # Check if message was posted to chatter
        self.assertEqual(len(self.invoice.message_ids), initial_msg_count + 1, "A message should be posted to chatter")
        self.assertIn("PDF generated successfully", self.invoice.message_ids[0].body)
        self.assertTrue(self.invoice.message_ids[0].attachment_ids, "The message should have an attachment")
        self.assertTrue(self.invoice.message_ids[0].attachment_ids[0].is_background_pdf)


    def test_03_threading_trigger(self):
        """Test if the public method correctly triggers a daemon thread."""
        with patch('threading.Thread') as mock_thread:
            self.env['ir.actions.report'].generate_in_background('fake_report', [1], request_id='req_123')
            
            mock_thread.assert_called_once()
            # Verify the call arguments
            args, kwargs = mock_thread.call_args
            # Verify the call arguments using __name__ to avoid bound method comparison issues
            self.assertEqual(kwargs['target'].__name__, '_generate_pdf_thread')
            self.assertEqual(kwargs['args'], ('fake_report', [1], None, 'req_123', False))
            self.assertTrue(mock_thread.return_value.daemon, "Thread should be a daemon")
            mock_thread.return_value.start.assert_called_once()

    def test_04_account_report_background(self):
        """Test the background generation for Enterprise Accounting Reports."""
        # Check if we can find any account.report
        report = self.env['account.report'].search([], limit=1)
        if not report:
            self.skipTest("No account.report found (Enterprise accounting may not be installed)")

        options = {'report_id': report.id, 'date': {'date_to': '2026-12-31'}}
        
        with patch.object(Registry, 'cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value = self.env.cr
            with patch.object(self.env.cr, 'commit'), patch.object(self.env.cr, 'rollback'):
                with patch.object(type(self.env['bus.bus']), '_sendone') as mock_sendone:
                    # Mock export_to_pdf to avoid heavy rendering
                    with patch.object(type(report), 'export_to_pdf', create=True, return_value={'file_content': b'PDF CONTENT'}):
                        self.env['account.report']._generate_pdf_thread(options, request_id='acc_req_1')

                    # 1. Check attachment
                    attachment = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.report'),
                        ('res_id', '=', report.id),
                        ('is_background_pdf', '=', True)
                    ])
                    self.assertTrue(attachment)
                    self.assertIn(report.name, attachment.name)

                    # 2. Check bus notification
                    mock_sendone.assert_called_once()
                    _, channel, data = mock_sendone.call_args[0]
                    self.assertEqual(channel, 'pdf_download')
                    self.assertEqual(data['request_id'], 'acc_req_1')

    def test_05_error_handling(self):
        """Test if errors during background generation are captured and notified via the bus."""
        report_name = 'non.existent.report'
        docids = [1]

        with patch.object(Registry, 'cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value = self.env.cr
            with patch.object(self.env.cr, 'commit'), patch.object(self.env.cr, 'rollback'):
                # Use type() here to avoid read-only property error in Odoo 18
                with patch.object(type(self.env['bus.bus']), '_sendone') as mock_sendone:
                    # This should raise an exception because the report doesn't exist
                    self.env['ir.actions.report']._generate_pdf_thread(report_name, docids, tab_id='tab_err')

                    # Check if error notification was sent
                    mock_sendone.assert_called_once()
                    _, channel, data = mock_sendone.call_args[0]
                    self.assertEqual(channel, 'pdf_error')
                    self.assertEqual(data['tab_id'], 'tab_err')
                    self.assertEqual(data['title'], 'PDF Generation Failed')
