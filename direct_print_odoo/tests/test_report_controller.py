# -*- coding: utf-8 -*-
import logging
from types import SimpleNamespace
from unittest.mock import patch

from werkzeug.wrappers import Response

from odoo.addons.web.controllers.report import ReportController
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.direct_print_odoo.controllers import direct_print_odoo

logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestReportController(TransactionCase):
    """Check that PrintNode printing preserves Odoo's report response."""

    def test_pdf_report_is_returned_and_sent_to_printer(self):
        printer = self.env['printer.details'].create({
            'id_of_printer': '42',
            'printers_name': 'Test printer',
        })
        self.env.company.write({
            'api_key_print_node': 'test_api_key',
            'is_multiple_printers': False,
            'available_printers_id': printer.id,
        })
        pdf_response = Response(b'%PDF-test', mimetype='application/pdf')
        fake_request = SimpleNamespace(
            env=SimpleNamespace(company=self.env.company)
        )

        with (
            patch.object(ReportController, 'report_routes',
                         return_value=pdf_response) as render_report,
            patch.object(direct_print_odoo, 'request', fake_request),
            patch.object(direct_print_odoo, 'Gateway') as gateway_class,
        ):
            response = direct_print_odoo.ReportControllers().report_routes(
                'test.report', converter='pdf'
            )

        self.assertIs(response, pdf_response)
        render_report.assert_called_once()
        gateway_class.return_value.PrintJob.assert_called_once()
        self.assertEqual(
            gateway_class.return_value.PrintJob.call_args.kwargs['printer'],
            42,
        )

        logger.info("PASSED : test_pdf_report_is_returned_and_sent_to_printer")
