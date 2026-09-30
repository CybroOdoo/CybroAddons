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
import json
from unittest.mock import Mock, patch

from requests.auth import HTTPBasicAuth

from odoo.tests.common import TransactionCase, tagged


class DummyElapsed:
    def total_seconds(self):
        return 0.25


class DummyResponse:
    def __init__(self, status_code=200, reason='OK', json_data=None, text='', headers=None, content=b''):
        self.status_code = status_code
        self.reason = reason
        self._json_data = json_data
        self.text = text
        self.headers = headers or {'Content-Type': 'application/json'}
        self.elapsed = DummyElapsed()
        self.content = content

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


@tagged('post_install', '-at_install')
class TestAPIWorkflowTesting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Workflow = cls.env['api.workflow']
        cls.workflow = cls.Workflow.create({'name': 'Workflow Testing Helpers'})

    def test_url_header_success_and_query_helpers(self):
        self.assertEqual(self.workflow._join_url('https://example.com/api/', '/products'), 'https://example.com/api/products')
        self.assertEqual(self.workflow._join_url('https://example.com', 'https://other.test/path'), 'https://other.test/path')
        self.assertTrue(self.workflow._is_success('204'))
        self.assertFalse(self.workflow._is_success('500'))
        self.assertFalse(self.workflow._is_success('bad'))

        headers = self.workflow._setup_request_headers({'headers': [{'key': 'X-Test', 'value': '1'}]})
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['X-Test'], '1')

        url = self.workflow._build_url_with_query_params(
            'https://example.com/items?page=1',
            {'query_params': {'filter': 'new', 'page': '2'}},
        )
        self.assertIn('filter=new', url)
        self.assertIn('page=2', url)

    def test_auth_helpers(self):
        basic = self.workflow._setup_basic_auth({'username': 'u', 'password': 'p'})
        self.assertIsInstance(basic, HTTPBasicAuth)
        self.assertIsNone(self.workflow._setup_basic_auth({'username': 'u'}))

        auth_obj, headers = self.workflow._get_auth_object({'authType': 'bearer', 'token': 'abc'})
        self.assertIsNone(auth_obj)
        self.assertEqual(headers['Authorization'], 'Bearer abc')

        auth_obj, headers = self.workflow._get_auth_object({
            'authType': 'api-key',
            'keyLocation': 'header',
            'keyName': 'X-Key',
            'apiKey': 'secret',
        })
        self.assertIsNone(auth_obj)
        self.assertEqual(headers['X-Key'], 'secret')

        auth_obj, headers = self.workflow._handle_authentication({}, 'none', {
            'apiPlatform': 'shopify',
            'apiKey': 'shop-token',
        })
        self.assertIsNone(auth_obj)
        self.assertEqual(headers['X-Shopify-Access-Token'], 'shop-token')

    def test_content_type_and_body_preparation(self):
        self.assertEqual(
            self.workflow._get_content_type({}, {'body': '{"a": 1}'}),
            'application/json',
        )
        self.assertEqual(
            self.workflow._get_content_type({}, {'body': 'a=1'}),
            'application/x-www-form-urlencoded',
        )
        self.assertEqual(self.workflow._prepare_request_data({'body': '{"a": 1}'}), {'a': 1})
        self.assertEqual(self.workflow._prepare_request_data({'body': 'not json'}), 'not json')
        self.assertEqual(self.workflow._prepare_post_request_data({'body': '{"a": 1}'}), {'a': 1})
        self.assertEqual(
            self.workflow._prepare_post_request_data({'body': {'file': 'x'}, 'contentType': 'multipart/form-data'}),
            {'file': 'x'},
        )
        self.assertEqual(self.workflow._prepare_put_request_data({'body': '{"b": 2}'}), {'b': 2})

    def test_final_url_platform_builders(self):
        shopify = self.workflow._build_final_url('https://shop.myshopify.com/products', 'none', {'apiPlatform': 'shopify'})
        self.assertEqual(shopify, 'https://shop.myshopify.com/admin/api/2024-10/products.json')

        woo_config = {'apiPlatform': 'woocommerce', 'authType': 'basic', 'username': 'ck', 'password': 'cs'}
        woocommerce = self.workflow._build_final_url('https://store.test/products', 'basic', woo_config)
        self.assertIn('/wp-json/wc/v3/products', woocommerce)
        self.assertIn('consumer_key=ck', woocommerce)
        self.assertIn('consumer_secret=cs', woocommerce)

        hubspot = self.workflow._build_final_url('https://api.hubapi.com/contacts', 'none', {'apiPlatform': 'hubspot'})
        self.assertEqual(hubspot, 'https://api.hubapi.com/crm/v3/objects/contacts')

    def test_response_parsing(self):
        response = DummyResponse(json_data={'ok': True}, text='{"ok": true}')
        parsed = self.workflow._parse_successful_response(response, 'https://example.com')
        self.assertTrue(parsed['success'])
        self.assertEqual(parsed['data'], {'ok': True})
        self.assertEqual(parsed['response_time'], 0.25)

        html_response = DummyResponse(text='<html></html>', json_data=ValueError())
        parsed = self.workflow._parse_successful_response(html_response, 'https://example.com')
        self.assertFalse(parsed['success'])

        failed = self.workflow._parse_failed_response('https://example.com', 'timeout while connecting')
        self.assertFalse(failed['success'])
        self.assertEqual(failed['status_code'], 'TIMEOUT')

    def test_execute_request_uses_expected_request_arguments(self):
        with patch('odoo.addons.odoo_integration_workflow.models.workflow_testing.requests.request') as mocked:
            mocked.return_value = DummyResponse()
            self.workflow._execute_request(
                'post',
                'https://shop.myshopify.com/admin/api/products.json',
                {'Content-Type': 'application/json'},
                {'name': 'A'},
                None,
                {'apiPlatform': 'shopify', 'timeout': '5'},
            )

        kwargs = mocked.call_args.kwargs
        self.assertEqual(kwargs['method'], 'POST')
        self.assertEqual(kwargs['json'], {'name': 'A'})
        self.assertEqual(kwargs['timeout'], 5.0)
        self.assertEqual(kwargs['url'], 'https://shop.myshopify.com/admin/api/2024-10/products.json')

    def test_endpoint_and_connected_node_discovery(self):
        nodes = [
            {'id': 'ep', 'type': 'endpoint', 'config': {'baseUrl': 'https://store.test', 'apiPlatform': 'woocommerce', 'authType': 'basic'}},
            {'id': 'get1', 'type': 'get', 'config': {'url': '/products'}},
        ]
        endpoint, base_url, endpoint_id = self.workflow._find_endpoint_and_base_url(nodes)
        self.assertEqual(endpoint, nodes[0])
        self.assertEqual(base_url, 'https://store.test/wp-json/wc/v3')
        self.assertEqual(endpoint_id, 'ep')

        connected = self.workflow._find_connected_api_nodes(nodes, [{'source': 'ep', 'target': 'get1'}], 'ep')
        self.assertEqual(len(connected), 1)
        self.assertEqual(connected[0]['config']['authType'], 'basic')
        self.assertEqual(connected[0]['config']['url'], '/products')

    def test_api_node_wrappers(self):
        node = {'id': 'get1', 'type': 'get', 'config': {}}

        with patch.object(type(self.workflow), '_test_url', return_value={
            'status_code': 200,
            'success': True,
            'data': {'ok': True},
            'headers': {},
            'response_time': 0.1,
        }):
            result = self.workflow._test_get_node(node, 'https://example.com', {}, 'none')
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['response_data']['ok'])

        with patch.object(type(self.workflow), '_test_post_url', return_value={
            'status_code': 201,
            'success': True,
            'data': {'id': 1},
            'headers': {},
            'response_time': 0.1,
        }):
            result = self.workflow._test_post_node({'id': 'post1'}, 'https://example.com', {}, 'none')
        self.assertTrue(result['success'])

        with patch.object(type(self.workflow), '_make_api_call_with_auth', return_value={'status_code': 204}):
            result = self.workflow._test_other_node({'id': 'put1'}, 'https://example.com', 'put', {}, 'none')
        self.assertEqual(result['node_type'], 'put')
        self.assertEqual(result['status'], 'success')

    def test_test_url_and_post_put_delete_methods_use_patched_requests(self):
        with patch('odoo.addons.odoo_integration_workflow.models.workflow_testing.requests.get', return_value=DummyResponse(json_data={'ok': True})) as mocked:
            result = self.workflow._test_url('https://example.com', config={'verify_ssl': False})
        self.assertTrue(result['success'])
        self.assertEqual(mocked.call_args.kwargs['verify'], False)

        with patch.object(type(self.workflow), '_execute_request', return_value=DummyResponse(status_code=201, reason='Created', json_data={'id': 1})):
            result = self.workflow._test_post_url('https://example.com', config={'body': '{"name": "A"}'})
        self.assertTrue(result['success'])

        with patch('odoo.addons.odoo_integration_workflow.models.workflow_testing.requests.put', return_value=DummyResponse(json_data={'ok': True})):
            result = self.workflow._test_put_url('https://example.com', config={'body': '{"name": "B"}'})
        self.assertTrue(result['success'])

        with patch('odoo.addons.odoo_integration_workflow.models.workflow_testing.requests.delete', return_value=DummyResponse(json_data={'deleted': True})):
            result = self.workflow._test_delete_url('https://example.com')
        self.assertTrue(result['success'])

    def test_make_api_call_and_exception_handler(self):
        with patch.object(type(self.workflow), '_execute_request', return_value=DummyResponse(status_code=200, json_data={'ok': True})):
            result = self.workflow._make_api_call_with_auth('https://example.com', 'get', {}, 'none')

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['response_data'], {'ok': True})

        error = self.workflow._handle_api_call_exception('https://example.com', 'get', 'boom')
        self.assertEqual(error['status'], 'error')
        self.assertEqual(error['status_code'], None)

    def test_json_path_variables_and_comparisons(self):
        data = {'items': [{'name': 'A'}], 'total': '3'}
        self.assertEqual(self.workflow._extract_json_path_value(data, '$.items[0].name'), 'A')
        self.assertIsNone(self.workflow._extract_json_path_value(data, '$.items[5].name'))

        context = {'data': [{'title': 'Chair'}], 'price': 10}
        self.assertEqual(self.workflow._substitute_variables('{{ data[0].title }}', context), 'Chair')
        self.assertEqual(self.workflow._substitute_variables({'amount': '{{ price }}'}, context), {'amount': 10})
        self.assertEqual(self.workflow._get_variable_value('data.0.title', context), 'Chair')

        self.assertTrue(self.workflow._perform_comparison('10', '2', 'greater_than'))
        self.assertTrue(self.workflow._evaluate_condition('10', 'greater_than', '2'))
        self.assertEqual(self.workflow._auto_convert('false'), False)
        self.assertEqual(self.workflow._auto_convert('3.5'), 3.5)

    def test_condition_helpers(self):
        context = {'item': {'qty': 5}, 'threshold': 3}
        condition = {
            'id': 'cond1',
            'type': 'condition',
            'config': {'leftOperand': 'qty', 'operator': 'greater_than', 'rightOperand': '{{ threshold }}'},
        }
        result = self.workflow._evaluate_condition_in_loop(condition, context)
        self.assertTrue(result['condition_result'])
        self.assertEqual(self.workflow._get_nested_value(context, 'item.qty'), 5)

        source_result = {'status': 'success', 'node_type': 'condition', 'condition_result': True}
        self.assertTrue(self.workflow._should_connection_be_active({'outputType': 'true'}, source_result))
        self.assertFalse(self.workflow._should_connection_be_active({'outputType': 'false'}, source_result))

    def test_orm_node_create_search_read_write_count_and_unlink(self):
        create_node = {
            'id': 'orm_create',
            'type': 'orm',
            'config': {
                'model': 'res.partner',
                'operation': 'create',
                'field_values_json': json.dumps({'name': 'ORM Node Partner'}),
            },
        }
        create_result = self.workflow._run_orm_node(create_node, {})
        self.assertTrue(create_result['success'])

        partner_id = create_result['response_data']['id']
        write_node = {
            'id': 'orm_write',
            'type': 'orm',
            'config': {
                'model': 'res.partner',
                'operation': 'write',
                'record_id': partner_id,
                'field_values_json': json.dumps({'name': 'ORM Node Partner Updated'}),
            },
        }
        self.assertTrue(self.workflow._run_orm_node(write_node, {})['success'])

        read_node = {
            'id': 'orm_read',
            'type': 'orm',
            'config': {
                'model': 'res.partner',
                'operation': 'read',
                'record_id': partner_id,
                'fields': 'name',
            },
        }
        read_result = self.workflow._run_orm_node(read_node, {})
        self.assertEqual(read_result['response_data'][0]['name'], 'ORM Node Partner Updated')

        count_node = {
            'id': 'orm_count',
            'type': 'orm',
            'config': {
                'model': 'res.partner',
                'operation': 'search_count',
                'field_values_json': json.dumps([['id', '=', partner_id]]),
            },
        }
        self.assertEqual(self.workflow._run_orm_node(count_node, {})['response_data']['count'], 1)

        unlink_node = {
            'id': 'orm_unlink',
            'type': 'orm',
            'config': {
                'model': 'res.partner',
                'operation': 'unlink',
                'record_id': partner_id,
                'field_values_json': '[]',
            },
        }
        self.assertTrue(self.workflow._run_orm_node(unlink_node, {})['success'])
        self.assertFalse(self.env['res.partner'].browse(partner_id).exists())

    def test_test_single_node_routes_supported_types(self):
        with patch.object(type(self.workflow), '_execute_api_node', return_value={'success': True, 'status': 'success'}):
            result = self.Workflow.test_single_node({'id': 'get1', 'type': 'get', 'config': {'url': 'https://example.com'}})
        self.assertTrue(result['success'])

        result = self.Workflow.test_single_node({'id': 'x', 'type': 'unsupported', 'config': {}})
        self.assertFalse(result['success'])

        result = self.Workflow.test_single_node('not a dict')
        self.assertFalse(result['success'])

    def test_test_workflow_executes_start_node_without_network(self):
        result = self.Workflow.test_workflow({
            'nodes': [{'id': 'start', 'type': 'start', 'config': {}}],
            'connections': [],
        })

        self.assertTrue(result['success'])
        self.assertEqual(result['results'][0]['node_id'], 'start')

    def test_endpoint_node_complete_with_patched_request(self):
        with patch('odoo.addons.odoo_integration_workflow.models.workflow_testing.requests.get', return_value=DummyResponse(status_code=200, json_data={'ok': True})):
            result = self.workflow._test_endpoint_node_complete(
                {'id': 'ep1', 'type': 'endpoint'},
                {'baseUrl': 'https://example.com', 'apiPlatform': 'generic'},
            )

        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 200)

        result = self.workflow._test_endpoint_node_complete({'id': 'ep1'}, {'baseUrl': ''})
        self.assertFalse(result['success'])

    def test_flatten_and_create_node_results(self):
        flat = self.workflow._flatten_results([{'node_id': 'a'}, [{'node_id': 'b'}]])
        self.assertEqual([item['node_id'] for item in flat], ['a', 'b'])

        node_results = self.workflow._create_node_results([
            {'node_id': 'a', 'status': 'success', 'data': {'ok': True}},
            {'node_id': 'b', 'status': 'error', 'error': 'boom'},
        ])
        self.assertTrue(node_results[0]['success'])
        self.assertFalse(node_results[1]['success'])
