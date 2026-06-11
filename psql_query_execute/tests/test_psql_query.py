import io
import json
import zipfile

from odoo.tests import TransactionCase, tagged


class FakeResponse:

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestPsqlQuery(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.query = cls.env['psql.query'].create({
            'name': 'Partner Query',
            'query_name': (
                "SELECT 'Alpha'::varchar AS partner_name, "
                "7::integer AS partner_count"
            ),
        })

    def test_action_execute_query_sets_html_result(self):
        self.query.action_execute_query()

        self.assertIn('partner_name', self.query.query_result)
        self.assertIn('partner_count', self.query.query_result)
        self.assertIn('Alpha', self.query.query_result)
        self.assertIn('7', self.query.query_result)

    def test_get_report_data_returns_headers_and_rows(self):
        data = self.query._get_report_data()

        self.assertEqual(data['model'], 'psql.query')
        self.assertFalse(data['no_value'])
        self.assertEqual(data['header'], ['partner_name', 'partner_count'])
        self.assertEqual(data['form'], [('Alpha', 7)])
        self.assertEqual(data['ids'], self.query)
        self.assertTrue(data['date'])

    def test_action_print_query_result_xlsx(self):
        action = self.query.action_print_query_result_xlsx()
        report_data = action['data']
        options = json.loads(report_data['options'])

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(report_data['model'], 'psql.query')
        self.assertEqual(report_data['output_format'], 'xlsx')
        self.assertEqual(report_data['report_name'], 'Query Report')
        self.assertEqual(options['header'], ['partner_name', 'partner_count'])
        self.assertEqual(options['form'], [['Alpha', 7]])

    def test_get_xlsx_report_writes_workbook_to_response(self):
        response = FakeResponse()
        data = {
            'header': ['partner_name', 'partner_count'],
            'form': [('Alpha', 7), ({'nested': 'value'}, None)],
            'date': '2026-06-09',
        }

        self.query.get_xlsx_report(data, response)

        content = response.stream.getvalue()
        self.assertGreater(len(content), 0)
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(content)))
