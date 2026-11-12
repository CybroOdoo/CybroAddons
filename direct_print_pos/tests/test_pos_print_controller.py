# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import logging

import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon

logger = logging.getLogger(__name__)

ROUTE = '/pos/print_receipt_custom'
GATEWAY = 'odoo.addons.direct_print_pos.controllers.pos_print_controller.Gateway'
FAKE_PDF = b'%PDF-1.4 direct print pos test'


@tagged('post_install', '-at_install')
class TestPosPrintController(TestPointOfSaleHttpCommon):
    """Test cases for the /pos/print_receipt_custom route."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param(
            'direct_print_pos.enable_pos_templates', True)
        cls.main_pos_config.open_ui()
        cls.order = cls.env['pos.order'].create({
            'config_id': cls.main_pos_config.id,
            'session_id': cls.main_pos_config.current_session_id.id,
            'company_id': cls.main_pos_config.company_id.id,
            'amount_total': 10.0,
            'amount_paid': 10.0,
            'amount_tax': 0.0,
            'amount_return': 0.0,
            'to_invoice': False,
            'partner_id': False,
            'pricelist_id': cls.main_pos_config.pricelist_id.id,
            'pos_reference': '1000-004-00001',
            'name': 'Order Direct Print',
            'state': 'paid',
            'lines': [(0, 0, {
                'product_id': cls.desk_pad.product_variant_id.id,
                'price_unit': 10.0,
                'discount': 0,
                'qty': 1,
                'tax_ids': False,
                'price_subtotal': 10.0,
                'price_subtotal_incl': 10.0,
            })],
        })
        cls.printer_1, cls.printer_2, cls.printer_no_id = cls.env[
            'printer.details'].create([
                {'printers_name': 'Printer 1', 'id_of_printer': '101'},
                {'printers_name': 'Printer 2', 'id_of_printer': '102'},
                {'printers_name': 'Printer No ID', 'id_of_printer': False},
            ])
        # The route uses the company of the logged in POS user.
        cls.company = cls.pos_user.company_id
        cls.company.write({
            'api_key_print_node': 'test_api_key',
            'is_multiple_printers': False,
            'available_printers_id': cls.printer_1.id,
            'printers_ids': [(6, 0, (cls.printer_1 | cls.printer_2).ids)],
        })

    def setUp(self):
        super().setUp()
        self.authenticate('pos_user', 'pos_user')
        render_patcher = patch.object(
            self.registry['ir.actions.report'], '_render_qweb_pdf',
            return_value=(FAKE_PDF, 'pdf'))
        self.mock_render = render_patcher.start()
        self.addCleanup(render_patcher.stop)

    def _print(self, order_id):
        return self.make_jsonrpc_request(ROUTE, {'order_id': order_id})

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @patch(GATEWAY)
    def test_templates_disabled(self, mock_gateway_class):
        """Printing is refused when POS templates are not enabled."""
        for value in (False, 'False'):
            self.env['ir.config_parameter'].sudo().set_param(
                'direct_print_pos.enable_pos_templates', value)
            result = self._print(self.order.id)
            self.assertFalse(result['success'])
            self.assertEqual(result['error'],
                             'Please enable POS template in the settings.')
        mock_gateway_class.assert_not_called()
        self.mock_render.assert_not_called()
        logger.info('Passed : test_templates_disabled')

    @patch(GATEWAY)
    def test_missing_order_id(self, mock_gateway_class):
        """An order id is required."""
        result = self.make_jsonrpc_request(ROUTE, {})
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Order ID is required')
        mock_gateway_class.assert_not_called()
        logger.info('Passed : test_missing_order_id')

    @patch(GATEWAY)
    def test_unknown_order(self, mock_gateway_class):
        """An error is returned when the order does not exist."""
        missing_id = self.env['pos.order'].search(
            [], order='id desc', limit=1).id + 1000
        result = self._print(missing_id)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'],
                         f'Order with ID {missing_id} not found')
        mock_gateway_class.assert_not_called()
        self.mock_render.assert_not_called()
        logger.info('Passed : test_unknown_order')

    @patch(GATEWAY)
    def test_single_printer_not_configured(self, mock_gateway_class):
        """An error is returned when no printer is selected."""
        self.company.available_printers_id = False
        result = self._print(self.order.id)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Please select a printer.')
        mock_gateway_class.assert_not_called()
        logger.info('Passed : test_single_printer_not_configured')

    @patch(GATEWAY)
    def test_multiple_printers_not_configured(self, mock_gateway_class):
        """An error is returned when no printer with an id is selected."""
        self.company.write({
            'is_multiple_printers': True,
            'printers_ids': [(6, 0, self.printer_no_id.ids)],
        })
        result = self._print(self.order.id)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Please select at least one printer.')
        mock_gateway_class.assert_not_called()
        logger.info('Passed : test_multiple_printers_not_configured')

    # ------------------------------------------------------------------
    # Printing
    # ------------------------------------------------------------------
    @patch(GATEWAY)
    def test_print_single_printer(self, mock_gateway_class):
        """The receipt is rendered and sent to the selected printer."""
        result = self._print(self.order.id)
        self.assertEqual(result, {'success': True})

        self.mock_render.assert_called_once()
        report_ref, res_ids = self.mock_render.call_args.args[-2:]
        self.assertEqual(report_ref,
                         'direct_print_pos.action_report_pos_receipt_direct_print')
        self.assertEqual(res_ids, [self.order.id])

        mock_gateway_class.assert_called_once_with(
            url='https://api.printnode.com/', apikey='test_api_key')
        mock_gateway_class.return_value.PrintJob.assert_called_once_with(
            printer=101,
            options={'copies': 1},
            title=f'POS_{self.order.name}',
            job_type='pdf',
            base64=base64.b64encode(FAKE_PDF).decode('utf-8'),
        )
        logger.info('Passed : test_print_single_printer')

    @patch(GATEWAY)
    def test_print_multiple_printers(self, mock_gateway_class):
        """The receipt is sent to every selected printer having an id."""
        self.company.write({
            'is_multiple_printers': True,
            'printers_ids': [(6, 0, (self.printer_1 | self.printer_2
                                     | self.printer_no_id).ids)],
        })
        result = self._print(self.order.id)
        self.assertEqual(result, {'success': True})

        print_job = mock_gateway_class.return_value.PrintJob
        self.assertEqual(print_job.call_count, 2)
        self.assertEqual(
            sorted(call.kwargs['printer'] for call in print_job.call_args_list),
            [101, 102])
        logger.info('Passed : test_print_multiple_printers')

    @patch(GATEWAY)
    def test_print_printnode_failure(self, mock_gateway_class):
        """PrintNode errors are reported instead of raised."""
        mock_gateway_class.return_value.PrintJob.side_effect = Exception(
            'Invalid API Key')
        with self.assertLogs(
                'odoo.addons.direct_print_pos.controllers.pos_print_controller',
                level='ERROR'):
            result = self._print(self.order.id)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'],
                         'PrintNode request failed: Invalid API Key')
        logger.info('Passed : test_print_printnode_failure')

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    def test_receipt_template_render(self):
        """The receipt QWeb template renders the order details."""
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'direct_print_pos.action_report_pos_receipt_direct_print',
            self.order.ids)
        html = html.decode()
        self.assertIn(self.order.pos_reference, html)
        self.assertIn(self.desk_pad.product_variant_id.display_name, html)
        self.assertIn(self.order.company_id.name, html)
        logger.info('Passed : test_receipt_template_render')
