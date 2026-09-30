# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions @cybrosys(odoo@cybrosys.com)
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
#############################################################################
from odoo import models, api
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
import logging
import json
import requests
import collections

_logger = logging.getLogger(__name__)


class APIWorkflowTesting(models.AbstractModel):
    _name = 'api.workflow.testing'
    _description = 'API Workflow Testing Methods'


    def _join_url(self, base, path):
        """
        Helper to join base URL and path cleanly.
        Safety: If path is already a full URL, ignore base.
        """
        if not path:
            return base

        if path.startswith('http://') or path.startswith('https://'):
            return path

        if not base:
            return path

        return f"{base.rstrip('/')}/{path.lstrip('/')}"

    def _setup_request_headers(self, config):
        """Setup base headers with custom headers from config"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Odoo-API-Workflow/1.0'
        }

        custom_headers = config.get('headers', [])
        for header in custom_headers:
            headers[header['key']] = header['value']

        return headers

    def _is_success(self, status_code):
        """Safe success check for strings or integers"""
        if not status_code: return False
        try:
            code = int(status_code)
            return 200 <= code < 300
        except (ValueError, TypeError):
            return False


    def _build_url_with_query_params(self, url, config):
        """Build final URL with query parameters"""
        query_params = config.get('query_params', {})
        if not query_params:
            return url

        parsed_url = urlparse(url)
        existing_params = parse_qs(parsed_url.query)
        merged_params = {**existing_params, **query_params}
        query_string = urlencode(merged_params, doseq=True)

        final_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            query_string,
            parsed_url.fragment
        ))

        return final_url



    def _get_content_type(self, headers, config):
        """Determine the appropriate Content-Type header"""
        for key, value in headers.items():
            if key.lower() == 'content-type':
                return value

        content_type = config.get('contentType', 'application/json')

        body_content = config.get('body', '')
        if body_content:
            try:
                json.loads(body_content)
                return 'application/json'
            except (json.JSONDecodeError, TypeError):
                if isinstance(body_content, dict):
                    return 'application/json'
                else:
                    return 'application/x-www-form-urlencoded'

        return content_type

    def _prepare_request_data(self, config):
        """Prepare request data for POST/PUT requests"""
        body_content = config.get('body')
        if body_content:
            try:
                return json.loads(body_content)
            except json.JSONDecodeError:
                _logger.warning(f"Invalid JSON in request body: {body_content}")
                return body_content
        return None

    def _prepare_post_request_data(self, config):
        """Enhanced request data preparation for POST requests"""
        body_content = config.get('body')
        content_type = config.get('contentType', 'application/json')

        if not body_content:
            return None

        try:
            if content_type == 'application/json':
                if isinstance(body_content, str):
                    return json.loads(body_content)
                elif isinstance(body_content, dict):
                    return body_content
                else:
                    return str(body_content)

            elif content_type == 'application/x-www-form-urlencoded':
                if isinstance(body_content, str):
                    try:
                        parsed_json = json.loads(body_content)
                        return parsed_json
                    except json.JSONDecodeError:
                        return body_content
                elif isinstance(body_content, dict):
                    return body_content

            elif content_type == 'multipart/form-data':
                if isinstance(body_content, dict):
                    return body_content
                else:
                    return {'data': str(body_content)}

            else:
                return str(body_content)

        except Exception as e:
            _logger.warning(f"Error preparing POST request data: {str(e)}")
            return str(body_content)

    def _parse_api_response(self, url, response=None, error_message=None, method=None, node_id=None):
        """
        Unified API response parser. 
        Handles successful responses, HTTP errors, and connection exceptions.
        """
        data = None
        headers = {}
        response_time = 0
        status_code = None
        success = False
        reason = "Error"
        
        if response is not None:
            status_code = response.status_code
            success = 200 <= status_code < 300
            headers = dict(response.headers)
            response_time = response.elapsed.total_seconds()
            reason = getattr(response, 'reason', 'Error')
            
            try:
                if status_code == 204 or not response.text.strip():
                    data = ""
                else:
                    data = response.json()
            except (ValueError, AttributeError):
                data = getattr(response, 'text', '')
                if data and ("<!DOCTYPE html>" in data.lower() or "<html>" in data.lower()):
                    success = False
        else:
            # Handle exception case (no response object)
            status_code = "CONN_ERR"
            if error_message:
                if "SSL" in error_message: status_code = "SSL_ERR"
                elif "timeout" in error_message.lower(): status_code = "TIMEOUT"
            reason = error_message or "Connection Error"

        status = 'success' if success else 'error'
        message = f'HTTP {status_code} - {reason}' if response is not None else f"Request failed: {reason}"

        return {
            'node_id': node_id,
            'success': success,
            'status': status,
            'status_code': status_code,
            'message': message,
            'url': url,
            'method': method,
            'data': data,
            'response_data': data,  # Key used by some older methods
            'response_time': response_time,
            'headers': headers,
            'error': error_message if response is None else None
        }

    def _execute_request(self, method, url, headers, data, auth, config):
        """
        Executes HTTP requests with Safe Timeout & Platform Logic.
        """
        platform = config.get('apiPlatform', 'generic')
        target_url = url.strip()

        if platform == 'shopify':
            parsed = urlparse(target_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            path_parts = parsed.path.split('/')
            resource_segment = path_parts[-1] if path_parts else 'products'
            resource = resource_segment.replace('.json', '')

            if not resource or resource == 'api':
                resource = 'products'

            target_url = f"{domain}/admin/api/2024-10/{resource}.json"


        try:
            raw_timeout = config.get('timeout', 10)
            timeout = float(raw_timeout)
        except (ValueError, TypeError):
            timeout = 10.0

        json_data = None
        body_data = None


        if headers.get('Content-Type') == 'application/json':
            json_data = data
        else:
            body_data = data


        response = requests.request(
            method=method.upper(),
            url=target_url,
            headers=headers,
            json=json_data,
            data=body_data,
            auth=auth,
            timeout=timeout,
            verify=False,
            allow_redirects=False
        )
        return response


    def _test_url(self, url, headers=None, auth_type='none', config=None):
        """Execute the Request with Debugging"""
        config = config or {}
        headers = headers or {}

        if auth_type == 'none' and config.get('authType'):
            auth_type = config.get('authType')

        try:
            auth_obj, headers = self._handle_authentication(headers, auth_type, config)

            final_url = self._build_final_url(url, auth_type, config)



            response = requests.get(
                final_url,
                headers=headers,
                auth=auth_obj,
                timeout=10,
                verify=config.get('verify_ssl', True)
            )


            return self._parse_api_response(url, response=response)

        except requests.exceptions.RequestException as e:
            return self._parse_api_response(url, error_message=str(e))
        except Exception as e:
            return self._parse_api_response(url, error_message=str(e))


    def _test_post_url(self, url, headers=None, auth_type='none', config=None):
        """Execute a POST request with the given configuration."""
        config = config or {}
        headers = headers or {}

        auth_obj, headers = self._handle_authentication(headers, auth_type, config)

        final_url = self._build_final_url(url, auth_type, config)

        content_type = self._get_content_type(headers, config)
        headers['Content-Type'] = content_type
        data = self._prepare_post_request_data(config)

        response = self._execute_request('POST', final_url, headers, data, auth_obj, config)

        try:
            return self._parse_api_response(final_url, response=response, method='POST')
        except:
            error_msg = f"Request failed (HTTP {response.status_code}). Response was not JSON."
            return self._parse_api_response(final_url, response=response, error_message=error_msg, method='POST')


    def _parse_successful_response(self, response, url):
        """Ensures success is only True if we get JSON, not HTML theme code.
        Handles 204 No Content as a success case."""
        data = None
        success = 200 <= response.status_code < 300

        # Special Case: 204 No Content or empty string
        if response.status_code == 204 or not response.text.strip():
            data = ""
            # success remains True because of the range check above
        else:
            try:
                data = response.json()
                # success remains True
            except ValueError:
                data = response.text
                if "<!DOCTYPE html>" in data.lower() or "<html>" in data.lower():
                    success = False

        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'data': data,
            'response_time': response.elapsed.total_seconds(),
            'success': success
        }

    def _parse_failed_response(self, url, error_message, node_id=None):
        """Enhanced failure parsing to avoid 'HTTP None' in the UI"""
        _logger.error(f"Request failed for {url}: {error_message}")

        code_label = "CONN_ERR"
        if "SSL" in error_message:
            code_label = "SSL_ERR"
        elif "timeout" in error_message.lower():
            code_label = "TIMEOUT"

        return {
            'node_id': node_id,
            'success': False,
            'status': 'error',
            'status_code': code_label,
            'data': None,
            'message': f"Request failed: {error_message}",
            'error': error_message,
            'response_time': 0
        }


    def _handle_authentication(self, headers, auth_type, config):
        """Handle authentication headers based on the platform and configuration."""
        platform = config.get('apiPlatform', 'generic')

        if platform == 'shopify':
            token = config.get('apiKey')
            if token:
                headers['X-Shopify-Access-Token'] = token
            return None, headers  # Return None to stop Odoo from adding Basic Auth headers

        auth_obj, extra_headers = self._get_auth_object(config)
        if extra_headers:
            headers.update(extra_headers)
        return auth_obj, headers


    def _build_final_url(self, url, auth_type, config):
        """
        URL BUILDER: Forces correct paths for Shopify and WooCommerce.
        """
        final_url = (url or "").strip()
        platform = config.get('apiPlatform', 'generic')

        if platform == 'shopify':
            parsed = urlparse(final_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            clean_path = parsed.path.replace('/admin/api/2024-10', '').replace('/admin/api/2024-01', '').lstrip('/')

            final_url = f"{domain}/admin/api/2024-10/{clean_path}"

            if not final_url.endswith('.json'):
                if '?' in final_url:
                    u_parts = final_url.split('?')
                    if not u_parts[0].endswith('.json'):
                        final_url = f"{u_parts[0]}.json?{u_parts[1]}"
                else:
                    final_url = f"{final_url}.json"
        elif platform == 'woocommerce':
            if 'wp-json' not in final_url:
                parsed = urlparse(final_url)
                final_url = f"{parsed.scheme}://{parsed.netloc}/wp-json/wc/v3/{parsed.path.lstrip('/')}"

            safe_auth_type = (auth_type or '').lower()
            if safe_auth_type == 'basic':
                username = config.get('username') or config.get('apiKey')
                password = config.get('password') or config.get('secretKey')
                if username and password:
                    if 'query_params' not in config: config['query_params'] = {}
                    config['query_params']['consumer_key'] = username
                    config['query_params']['consumer_secret'] = password
        elif platform == 'hubspot':
            parsed = urlparse(final_url)
            path = parsed.path.lstrip('/')

            if 'crm/v3' not in path:
                path = f"crm/v3/{path}"

            standard_objects = ['contacts', 'companies', 'deals', 'tickets', 'products', 'quotes', 'line_items']
            path_parts = path.split('/')
            
            if path_parts[-1] in standard_objects and 'objects' not in path_parts:
                idx = path_parts.index('v3') + 1 if 'v3' in path_parts else 0
                path_parts.insert(idx, 'objects')
                path = "/".join(path_parts)

            final_url = f"{parsed.scheme}://{parsed.netloc}/{path.lstrip('/')}"
            
            if parsed.query:
                final_url = f"{final_url}?{parsed.query}"


        return self._build_url_with_query_params(final_url, config)


    def _make_api_call_with_auth(self, url, method, config, auth_type):
        """Make API call with authentication support"""
        try:
            headers = self._setup_request_headers(config)
            auth_obj, headers = self._handle_authentication(headers, auth_type, config)
            final_url = self._build_final_url(url, auth_type, config)

            data = None
            if method == 'post':
                data = self._prepare_post_request_data(config)
            elif method == 'put':
                data = self._prepare_request_data(config)

            http_method = method.upper() if method != 'endpoint' else 'GET'

            response = self._execute_request(http_method, final_url, headers, data, auth_obj, config)
            return self._parse_api_response(final_url, response=response, method=http_method)

        except Exception as e:
            return self._parse_api_response(url, error_message=str(e), method=method)




    def _find_endpoint_and_base_url(self, nodes):
        """Find endpoint node and extract base URL with MULTI-PLATFORM Intelligence"""

        endpoint_node = next((n for n in nodes if n.get('type') == 'endpoint'), None)
        base_url = ''
        endpoint_id = None

        if endpoint_node:
            endpoint_id = endpoint_node['id']
            config = endpoint_node.get('config', {})
            raw_url = config.get('baseUrl', '').strip().rstrip('/')
            platform = config.get('apiPlatform', 'generic')


            if platform == 'woocommerce':
                if 'wp-json' not in raw_url:
                    base_url = f"{raw_url}/wp-json/wc/v3"
                else:
                    base_url = raw_url


            elif platform == 'shopify':
                if '/admin/api' not in raw_url:
                    base_url = f"{raw_url}/admin/api/2024-10"
                else:
                    base_url = raw_url

            elif platform == 'hubspot':
                if not raw_url or 'api.hubapi.com' in raw_url:
                    base_url = "https://api.hubapi.com/crm/v3"
                elif '/crm/v3' not in raw_url:
                    base_url = f"{raw_url}/crm/v3"
                else:
                    base_url = raw_url


            elif platform == 'bigcommerce':
                if 'api.bigcommerce.com' in raw_url and '/v3' not in raw_url:
                    base_url = f"{raw_url}/v3"
                else:
                    base_url = raw_url

            else:
                base_url = raw_url


        return endpoint_node, base_url, endpoint_id

    def _find_connected_api_nodes(self, nodes, connections, endpoint_id):
        """Find all API nodes connected to the endpoint node"""
        connected_api_nodes = []
        endpoint_config = {}

        endpoint_node = next((n for n in nodes if n['id'] == endpoint_id), None)
        endpoint_config = endpoint_node.get('config', {}) if endpoint_node else {}

        if endpoint_node:
            endpoint_config = endpoint_node.get('config', {})


        for conn in connections:
            if conn['source'] == endpoint_id:
                target_node = next((n for n in nodes if n['id'] == conn['target']), None)
                if target_node and target_node.get('type') in ['get', 'post', 'put', 'delete']:
                    original_config = target_node.get('config', {})
                    merged_config = {**endpoint_config, **original_config}
                    connected_node = target_node.copy()
                    connected_node['config'] = merged_config
                    connected_api_nodes.append(connected_node)

                elif conn['target'] == endpoint_id:
                    source_node = next((n for n in nodes if n['id'] == conn['source']), None)
                    if source_node and source_node.get('type') in ['get', 'post', 'put', 'delete']:

                        original_config = source_node.get('config', {})
                        merged_config = {**endpoint_config, **original_config}
                        connected_node = source_node.copy()
                        connected_node['config'] = merged_config
                        connected_api_nodes.append(source_node)
                for node in connected_api_nodes:
                    _logger.info(f"  - {node['id']} ({node.get('type')})")

        return connected_api_nodes

    def _test_get_node(self, node, full_url, config, auth_type, endpoint_config=None):
        """Test a GET node """

        try:
            # 1. Config Merge
            if auth_type == 'none' and endpoint_config:
                auth_type = endpoint_config.get('authType', 'none')
                config = {**endpoint_config, **config}


            headers = self._setup_request_headers(config)

            response_data = self._test_url(full_url, headers, auth_type, config)

            status_code = response_data.get('status_code')

            if not status_code:
                error_msg = response_data.get('error', 'Unknown Error')
                return {
                    'node_id': node['id'],
                    'node_type': 'get',
                    'status': 'error',
                    'message': f"Connection Error: {error_msg}",
                    'url': full_url,
                    'response_data': None,
                    'status_code': 0,
                    'success': False
                }

            is_success = response_data.get('success', False)
            status = 'success' if is_success else 'error'
            message = f'GET request successful - HTTP {status_code}' if is_success else f'GET request failed - HTTP {status_code}'

            return {
                'node_id': node['id'],
                'node_type': 'get',
                'status': status,
                'message': message,
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {})
            }

        except Exception as e:
            import traceback
            _logger.error(traceback.format_exc())
            return self._create_error_result(node, full_url, 'get', str(e))

    def _test_post_node(self, node, full_url, config, auth_type, endpoint_config=None):
        """Test a POST node"""
        try:
            if auth_type == 'none' and endpoint_config:
                auth_type = endpoint_config.get('authType', 'none')
                config = {**endpoint_config, **config}

            headers = self._setup_request_headers(config)
            response_data = self._test_post_url(full_url, headers, auth_type, config)

            status_code = response_data.get('status_code')
            is_success = response_data.get('success', False)
            
            status = 'success' if is_success else 'error'
            message = f'POST request {"successful" if is_success else "failed"} - HTTP {status_code}'

            return {
                'node_id': node['id'],
                'node_type': 'post',
                'status': status,
                'message': message,
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {}),
                'success': is_success
            }
        except Exception as e:
            return self._create_error_result(node, full_url, 'post', str(e))

    def _test_other_node(self, node, full_url, node_type, config, auth_type, endpoint_config=None):
        """Test other types of nodes (PUT, DELETE, etc.)"""
        if auth_type == 'none' and endpoint_config:
            auth_type = endpoint_config.get('authType', 'none')
            config = {**endpoint_config, **config}

        result = self._make_api_call_with_auth(full_url, node_type, config, auth_type)
        result['node_id'] = node['id']
        result['node_type'] = node_type

        if 'status' not in result:
            result['status'] = 'success' if result.get('status_code', 0) < 400 else 'error'

        return result

    def _create_error_result(self, node, full_url, node_type, error_message):
        """Create error result for failed API calls"""
        return {
            'node_id': node['id'],
            'node_type': node_type,
            'status': 'error',
            'message': f'{node_type.upper()} request failed: {error_message}',
            'url': full_url,
            'error': error_message
        }

    def _create_skipped_result(self, node):
        """Create result for skipped nodes"""
        return {
            'node_id': node['id'],
            'node_type': node.get('type', 'unknown'),
            'status': 'skipped',
            'message': 'Not an API node',
            'url': None
        }

    @api.model
    def test_single_node(self, node_data):
        """Test a single API node with Context Injection"""
        try:
            if isinstance(node_data, dict):
                node_id = node_data.get('id')
                node_type = node_data.get('type', 'get')
                config = node_data.get('config', {})
                previous_responses = node_data.get('previous_responses', {})
            else:
                return {'success': False, 'message': "Invalid data format"}


            context = {}

            for prev_id, prev_data in previous_responses.items():
                context[prev_id] = prev_data

            if previous_responses:
                last_key = list(previous_responses.keys())[-1]
                context['data'] = previous_responses[last_key]
                context['previous_data'] = previous_responses[last_key]

                if isinstance(context.get('data'), dict):
                    context.update(context['data'])


            if node_type == 'orm':
                mock_node = {'id': node_id, 'type': 'orm', 'config': config}
                return self._run_orm_node(mock_node, context)

            elif node_type == 'condition':
                mock_results_map = {
                    pid: {'status': 'success', 'response_data': pdata}
                    for pid, pdata in previous_responses.items()
                }
                mock_node = {'id': node_id, 'type': 'condition', 'config': config}
                return self._evaluate_condition_node(mock_node, mock_results_map)

            elif node_type in ['get', 'post', 'put', 'delete', 'endpoint']:
                url = config.get('url', '')
                auth_type = config.get('authType', 'none')

                return self._execute_api_node(
                    {'id': node_id, 'type': node_type, 'config': config},
                    base_url="",
                    endpoint_config={},
                    context=context
                )

            else:
                return {'success': False, 'message': f"Independent test not supported for {node_type}"}

        except Exception as e:
            _logger.error(f"Single node test failed: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f'Test failed: {str(e)}',
                'error': str(e)
            }

    def _get_auth_object(self, config):
        """
        Build authentication object globally for all requests.
        Handles Basic, Bearer, and API Key authentication with robust fallbacks.
        """
        auth_type = (config.get('authType') or '').lower()
        headers = {}

        if auth_type == 'basic':
            # Handle various credential keys for Basic Auth
            username = (config.get('username') or config.get('apiKey') or 
                        config.get('client_id') or config.get('api_key') or '')
            password = (config.get('password') or config.get('secretKey') or 
                        config.get('client_secret') or config.get('api_secret') or '')

            if username and password:
                return requests.auth.HTTPBasicAuth(username, password), headers
            return None, headers

        elif auth_type == 'bearer':
            token = config.get('token') or config.get('bearerToken') or config.get('apiKey')
            if token:
                headers['Authorization'] = f"Bearer {token}"
            return None, headers

        elif auth_type in ['api-key', 'api_key']:
            key_loc = config.get('keyLocation', 'header')
            key_name = config.get('keyName', 'X-API-Key')
            api_key = config.get('apiKey') or config.get('api_key')

            if key_loc == 'header' and api_key:
                headers[key_name] = api_key
            return None, headers

        return None, headers


    def _test_delete_url(self, url, headers=None, auth_type='none', config=None):
        """ DELETE method testing with Safe Timeout & URL Build"""
        config = config or {}
        headers = headers or {}

        try:
            auth_obj, headers = self._handle_authentication(headers, auth_type, config)
            final_url = self._build_final_url(url, auth_type, config)

            try:
                timeout = float(config.get('timeout', 10))
            except (ValueError, TypeError):
                timeout = 10.0



            response = requests.delete(
                final_url,
                headers=headers,
                auth=auth_obj,
                timeout=timeout,
                verify=config.get('verify_ssl', True)
            )


            return self._parse_successful_response(response, final_url)

        except Exception as e:
            _logger.error(f"DELETE Error: {e}")
            return self._parse_failed_response(url, str(e))



    def _test_put_url(self, url, headers=None, auth_type='none', config=None):
        """Enhanced PUT method testing with Safe Timeout & URL Build"""
        config = config or {}
        headers = headers or {}

        try:
            auth_obj, headers = self._handle_authentication(headers, auth_type, config)
            final_url = self._build_final_url(url, auth_type, config)


            try:
                timeout = float(config.get('timeout', 10))
            except (ValueError, TypeError):
                timeout = 10.0


            content_type = self._get_content_type(headers, config)
            headers['Content-Type'] = content_type
            data = self._prepare_put_request_data(config)



            response = requests.put(
                final_url,
                json=data if content_type == 'application/json' else None,
                data=data if content_type != 'application/json' else None,
                headers=headers,
                auth=auth_obj,
                timeout=timeout,
                verify=config.get('verify_ssl', True)
            )

            return self._parse_successful_response(response, final_url)

        except Exception as e:
            _logger.error(f"PUT Error: {e}")
            return self._parse_failed_response(url, str(e))


    def _prepare_put_request_data(self, config):
        """Enhanced request data preparation for PUT requests"""
        body_content = config.get('body')
        content_type = config.get('contentType', 'application/json')

        if not body_content:
            return None

        try:
            if content_type == 'application/json':
                if isinstance(body_content, str):
                    return json.loads(body_content)
                elif isinstance(body_content, dict):
                    return body_content
                else:
                    return str(body_content)

            elif content_type == 'application/x-www-form-urlencoded':
                if isinstance(body_content, str):
                    try:
                        parsed_json = json.loads(body_content)
                        return parsed_json
                    except json.JSONDecodeError:
                        return body_content
                elif isinstance(body_content, dict):
                    return body_content

            elif content_type == 'multipart/form-data':
                if isinstance(body_content, dict):
                    return body_content
                else:
                    return {'data': str(body_content)}

            else:
                return str(body_content)

        except Exception as e:
            _logger.warning(f"Error preparing PUT request data: {str(e)}")
            return str(body_content)

    def _perform_comparison(self, left_raw, right_raw, operator):
        """
        Compare two values with detailed logging and automatic type handling.
        """

        if operator == "exists":
            result = bool(left_raw)
            return result

        if operator == "does_not_exist":
            return not bool(left_raw)

        left = self._auto_convert(left_raw)
        right = self._auto_convert(right_raw)



        result = False

        try:
            if operator == "equals":
                result = str(left) == str(right)

            elif operator == "not_equals":
                result = str(left) != str(right)

            elif operator in ["greater_than", "less_than", "greater_equals", "less_equals"]:
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    if operator == "greater_than":
                        result = left > right
                    elif operator == "less_than":
                        result = left < right
                    elif operator == "greater_equals":
                        result = left >= right
                    elif operator == "less_equals":
                        result = left <= right
                else:
                    result = False

            elif operator == "contains":
                result = str(right) in str(left)

            elif operator == "starts_with":
                result = str(left).startswith(str(right))

            elif operator == "ends_with":
                result = str(left).endswith(str(right))

        except Exception as e:
            return False

        return result



    def _process_node_branch(self, current_node_id, nodes, connections, endpoint_config,
                             base_url, executed_nodes, node_results_map, results, flow_execution_data):
        """
        Recursively process a branch of the workflow
        """
        if current_node_id in executed_nodes:
            return

        executed_nodes.add(current_node_id)
        current_node = next((n for n in nodes if isinstance(n, dict) and n.get('id') == current_node_id), None)

        if not current_node:
            _logger.error(f' Node not found: {current_node_id}')
            return

        node_type = current_node.get('type')
        config = current_node.get('config', {})


        node_result = None
        if node_type in ['get', 'post', 'put', 'delete']:
            try:
                node_result = self._execute_api_node(current_node, base_url, endpoint_config)
                if isinstance(node_result, dict):
                    results.append(node_result)
                    node_results_map[current_node_id] = node_result
            except Exception as e:
                _logger.error(f'❌ API node execution failed but continuing: {current_node_id} - Error: {str(e)}')
                error_result = self._create_error_result(current_node, f"Execution failed: {str(e)}", node_type)
                results.append(error_result)
                node_results_map[current_node_id] = error_result

        elif node_type == 'condition':
            try:
                condition_result, evaluation_details = self._evaluate_condition_with_details_enhanced(
                    config, list(node_results_map.values()))

                node_result = {
                    'node_id': current_node_id,
                    'node_type': 'condition',
                    'status': 'success' if condition_result else 'condition_failed',
                    'message': f'Condition evaluated: {condition_result}',
                    'condition_result': condition_result,
                    'evaluation_details': evaluation_details,
                }
                results.append(node_result)
                node_results_map[current_node_id] = node_result

            except Exception as e:
                _logger.error(f'❌ Condition evaluation failed but continuing: {current_node_id} - Error: {str(e)}')
                error_result = {
                    'node_id': current_node_id,
                    'node_type': 'condition',
                    'status': 'error',
                    'message': f'Condition evaluation failed: {str(e)}',
                    'condition_result': False,
                    'evaluation_details': {'error': str(e)},
                }
                results.append(error_result)
                node_results_map[current_node_id] = error_result

        next_nodes = self._get_next_nodes(current_node_id, connections, node_results_map)

        for next_node_id in next_nodes:
            connection_data = {
                'source': current_node_id,
                'target': next_node_id,
                'outputType': self._get_connection_output_type(current_node_id, next_node_id, connections)
            }
            if not any(conn['source'] == connection_data['source'] and conn['target'] == connection_data['target']
                       for conn in flow_execution_data['executed_connections']):
                flow_execution_data['executed_connections'].append(connection_data)

        for next_node_id in next_nodes:
            self._process_node_branch(next_node_id, nodes, connections, endpoint_config,
                                      base_url, executed_nodes, node_results_map, results, flow_execution_data)

    def _get_connection_output_type(self, source_id, target_id, connections):
        """Get output type for a connection"""
        for conn in connections:
            if conn['source'] == source_id and conn['target'] == target_id:
                return conn.get('outputType')
        return None

    def _get_next_nodes(self, current_node_id, connections, node_results_map):
        """
        Get the next nodes to execute based on connections and conditions
        """
        next_nodes = []

        for conn in connections:
            if conn['source'] == current_node_id:
                source_node_result = node_results_map.get(current_node_id, {})
                source_node_type = source_node_result.get('node_type', 'unknown')

                if source_node_type == 'condition':
                    condition_result = source_node_result.get('condition_result')
                    output_type = conn.get('outputType')

                    if (condition_result is True and output_type == 'true') or \
                            (condition_result is False and output_type == 'false'):
                        next_nodes.append(conn['target'])
                else:
                    next_nodes.append(conn['target'])

        return next_nodes

    def _execute_api_node(self, node, base_url, endpoint_config, context=None):
        """
        Execute API node with proper configuration AND Variable Substitution
        """

        raw_config = node.get('config', {})

        if context:
            config = self._substitute_variables(raw_config, context)
        else:
            config = raw_config

        # 2. Prepare URL
        path = config.get('url', '')
        full_url = self._join_url(base_url, path)
        node_type = node.get('type', 'get')
        auth_type = config.get('authType', 'none')


        # 3. Merge Endpoint Config
        if auth_type == 'none' and endpoint_config:
            auth_type = endpoint_config.get('authType', 'none')
            # Note: We don't substitute endpoint config usually, but we merge it here
            config = {**endpoint_config, **config}

        try:
            if node_type == 'get':
                return self._test_get_node(node, full_url, config, auth_type, endpoint_config)
            elif node_type == 'post':
                return self._test_post_node(node, full_url, config, auth_type, endpoint_config)
            elif node_type == 'put':
                return self._test_put_node(node, full_url, config, auth_type, endpoint_config)
            elif node_type == 'delete':
                return self._test_delete_node(node, full_url, config, auth_type, endpoint_config)
            elif node_type == 'endpoint':
                return self._test_endpoint_node_complete(node, config)
            else:
                return self._create_skipped_result(node)

        except Exception as e:
            return self._create_error_result(node, full_url, node_type, str(e))


    def _flatten_results(self, results):
        """
        Flatten nested results structure to ensure we have a flat list of dictionaries
        """

        if not results:
            return []

        flattened = []

        def extract_dicts(item):
            """Recursively extract dictionary items from nested lists."""
            if isinstance(item, dict):
                flattened.append(item)
            elif isinstance(item, list):
                for subitem in item:
                    extract_dicts(subitem)

        extract_dicts(results)

        _logger.info(f"Flattened {len(flattened)} result dictionaries")
        for i, result in enumerate(flattened):
            _logger.info(f"  Result {i + 1}: {type(result)} - {result.get('node_id', 'No ID')}")

        return flattened


    def _execute_api_node_independently(self, node, base_url, endpoint_config):
        """
        Execute API node completely independently - never raise exceptions
        """
        config = node.get('config', {})
        node_type = node.get('type', 'get')

        if node_type == 'endpoint':
            base_url_to_test = config.get('baseUrl', '')
            return self._test_endpoint_node(node, base_url_to_test, config)

        path = config.get('url', '')
        full_url = self._join_url(base_url, path)


        try:
            if node_type == 'get':
                return self._test_get_node(node, full_url, config, config.get('authType', 'none'), endpoint_config)
            elif node_type == 'post':
                return self._test_post_node(node, full_url, config, config.get('authType', 'none'), endpoint_config)
            elif node_type == 'put':
                return self._test_put_node(node, full_url, config, config.get('authType', 'none'), endpoint_config)
            elif node_type == 'delete':
                return self._test_delete_node(node, full_url, config, config.get('authType', 'none'), endpoint_config)
            else:
                return self._create_skipped_result(node)

        except Exception as e:
            _logger.error(f'❌ Independent node execution failed: {node.get("id")} - {str(e)}')
            return self._create_error_result(node, full_url, node_type, str(e))

    def _test_endpoint_node(self, node, base_url, config):
        """
        Test endpoint node by checking if base URL is accessible
        """
        try:
            if not base_url:
                return {
                    'node_id': node['id'],
                    'node_type': 'endpoint',
                    'status': 'error',
                    'message': 'Missing base URL',
                    'url': base_url,
                    'error': 'Base URL not configured'
                }

            response = requests.head(base_url, timeout=10, verify=True)
            success = response.status_code < 400

            return {
                'node_id': node['id'],
                'node_type': 'endpoint',
                'status': 'success' if success else 'error',
                'message': f'Endpoint reachable - HTTP {response.status_code}' if success else f'Endpoint unreachable - HTTP {response.status_code}',
                'url': base_url,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'success': success
            }

        except Exception as e:
            return {
                'node_id': node['id'],
                'node_type': 'endpoint',
                'status': 'error',
                'message': f'Endpoint test failed: {str(e)}',
                'url': base_url,
                'error': str(e),
                'success': False
            }

    def _build_execution_order(self, start_node_id, nodes, connections):
        """
        Build execution order based on connection topology
        Returns list of node IDs in execution order
        """
        execution_order = []
        visited = set()

        def traverse(node_id):
            """Recursively traverse the graph to build execution order."""
            if node_id in visited:
                return
            visited.add(node_id)
            execution_order.append(node_id)

            next_nodes = []
            for conn in connections:
                if conn['source'] == node_id:
                    next_nodes.append(conn['target'])

            for next_id in sorted(next_nodes):
                traverse(next_id)

        traverse(start_node_id)
        return execution_order



    def _build_complete_execution_order(self, nodes, connections):
        """
        Build topological execution order based on connections
        """
        graph = {}
        all_nodes = set()
        node_types = {}

        for node in nodes:
            if isinstance(node, dict) and 'id' in node:
                node_id = node['id']
                all_nodes.add(node_id)
                graph[node_id] = []
                node_types[node_id] = node.get('type', 'unknown')

        for conn in connections:
            source = conn['source']
            target = conn['target']
            if source in graph:
                graph[source].append(target)
            else:
                graph[source] = [target]

            all_nodes.add(conn['source'])
            all_nodes.add(conn['target'])

        start_nodes = []
        has_incoming = set()

        for targets in graph.values():
            has_incoming.update(targets)

        for node_id in all_nodes:
            if node_id not in has_incoming:
                start_nodes.append(node_id)

        if not start_nodes:
            start_nodes = [n['id'] for n in nodes if isinstance(n, dict) and n.get('type') == 'start']
        if not start_nodes and nodes:
            start_nodes = [nodes[0]['id']] if isinstance(nodes[0], dict) and 'id' in nodes[0] else []

        execution_order = []
        visited = set()
        queue = collections.deque(start_nodes)

        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue

            visited.add(node_id)
            execution_order.append(node_id)

            for next_id in graph.get(node_id, []):
                if next_id not in visited:
                    queue.append(next_id)

        for node_id in all_nodes:
            if node_id not in visited:
                execution_order.append(node_id)

        return execution_order

    def _execute_single_node_independently(self, node_id, nodes, endpoint_config, base_url, node_results_map,
                                           connections):
        """
        Execute a single node completely independently - UPDATED
        """
        _logger.info('--------------------62--- SINGLE-NODE-EXECUTION --------------')
        current_node = next((n for n in nodes if isinstance(n, dict) and n.get('id') == node_id), None)

        if not current_node:
            return {
                'node_id': node_id,
                'node_type': 'unknown',
                'status': 'error',
                'message': 'Node not found',
                'error': 'Node configuration missing'
            }

        node_type = current_node.get('type')
        config = current_node.get('config', {})

        _logger.info(f' Executing node {node_id} ({node_type}) independently')

        try:
            if node_type == 'endpoint':
                return self._test_endpoint_node_complete(current_node, config)

            elif node_type in ['get', 'post', 'put', 'delete']:
                return self._test_api_node_independently(current_node, endpoint_config, base_url)

            elif node_type == 'condition':
                return self._evaluate_condition_independently(current_node, node_results_map, connections)

            elif node_type in ['start', 'end']:
                return {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'success',
                    'message': f'{node_type.capitalize()} node processed'
                }

            else:
                return {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'skipped',
                    'message': f'Unknown node type: {node_type}'
                }

        except Exception as e:
            _logger.error(f'❌ Independent execution failed for {node_id}: {str(e)}')
            return {
                'node_id': node_id,
                'node_type': node_type,
                'status': 'error',
                'message': f'Execution failed: {str(e)}',
                'error': str(e)
            }

    def _test_endpoint_node_complete(self, node, config):
        """Complete endpoint node testing with SMART VALIDATION & 401 Handling"""

        base_url = config.get('baseUrl', '').rstrip('/')
        node_id = node['id']
        auth_type = config.get('authType', 'none')
        platform = config.get('apiPlatform', 'generic')

        if not base_url:
            return {'node_id': node_id, 'status': 'error', 'message': 'Base URL not configured', 'success': False}

        try:
            test_url = base_url

            if platform == 'woocommerce' or 'wp-json' in base_url:
                if 'wp-json' not in test_url:
                    test_url = f"{base_url}/wp-json/wc/v3/products?per_page=1"
                elif 'products' not in test_url:
                    test_url = f"{test_url.rstrip('/')}/products?per_page=1"

            elif platform == 'shopify' or 'myshopify.com' in base_url:
                if '/admin/api' not in test_url:
                    test_url = f"{base_url}/admin/api/2024-01/shop.json"

            elif platform == 'bigcommerce' or 'api.bigcommerce.com' in base_url:
                if '/catalog/summary' not in test_url:
                    test_url = f"{base_url}/catalog/summary"

            elif platform == 'hubspot':
                test_url = f"{base_url}/crm/v3/objects/contacts?limit=1"


            headers = self._setup_request_headers(config)
            auth_obj, headers = self._handle_authentication(headers, auth_type, config)

            if 'api.bigcommerce.com' in base_url:
                headers['Accept'] = 'application/json'
                headers['Content-Type'] = 'application/json'

            final_url = self._build_final_url(test_url, auth_type, config)


            response = requests.get(
                final_url,
                headers=headers,
                auth=auth_obj,
                timeout=10,
                verify=False
            )

            if response.status_code in [401, 403]:
                return {
                    'node_id': node_id,
                    'node_type': 'endpoint',
                    'status': 'error',
                    'success': False,
                    'status_code': response.status_code,
                    'message': "Authentication not validated. Check API Key or Token.",
                    'error': "Invalid Consumer Key or Secret"
                }

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type and platform != 'generic':
                return {
                    'node_id': node_id,
                    'status': 'error',
                    'success': False,
                    'status_code': response.status_code,
                    'message': "Connection refused: Site returned HTML instead of API JSON. Check URL.",
                    'error': "HTML_RESPONSE_ERROR"
                }

            is_reachable = response.status_code < 400

            return {
                'node_id': node_id,
                'node_type': 'endpoint',
                'status': 'success' if is_reachable else 'error',
                'message': f'Connection Successful - HTTP {response.status_code}',
                'url': final_url,
                'status_code': response.status_code,
                'success': is_reachable,
                'response_data': {'note': 'Validated against protected endpoint'}
            }

        except Exception as e:
            return self._parse_failed_response(base_url, str(e), node_id)

    def _test_api_node_independently(self, node, endpoint_config, base_url):
        """Test API node with fallback to endpoint config"""
        config = node.get('config', {})
        node_type = node.get('type', 'get')
        node_id = node.get('id', 'unknown')
        path = config.get('url', '')

        if node_type == 'endpoint':
            full_url = config.get('baseUrl', '')
            if not full_url:
                return {
                    'node_id': node_id,
                    'node_type': 'endpoint',
                    'status': 'error',
                    'message': 'Base URL not configured',
                    'url': '',
                    'error': 'Missing base URL',
                    'success': False
                }
        else:
            if base_url and path:
                full_url = self._join_url(base_url, path)
            elif path.startswith(('http://', 'https://')):
                full_url = path
            else:
                full_url = path

        effective_config = config.copy()
        auth_type = config.get('authType', 'none')

        if auth_type == 'none' and endpoint_config:
            effective_config = {**endpoint_config, **config}

        try:
            if node_type == 'endpoint':
                response = requests.head(full_url, timeout=10, verify=True)
                success = response.status_code < 400

                return {
                    'node_id': node_id,
                    'node_type': 'endpoint',
                    'status': 'success' if success else 'error',
                    'message': f'Endpoint {"reachable" if success else "unreachable"} - HTTP {response.status_code}',
                    'url': full_url,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'success': success,
                    'response_data': {'reachable': success, 'status_code': response.status_code}
                }
            elif node_type == 'get':
                response_data = self._test_url(full_url, self._setup_request_headers(effective_config),
                                               effective_config.get('authType', 'none'), effective_config)
            elif node_type == 'post':
                response_data = self._test_post_url(full_url, self._setup_request_headers(effective_config),
                                                    effective_config.get('authType', 'none'), effective_config)
            elif node_type == 'put':
                response_data = self._test_put_url(full_url, self._setup_request_headers(effective_config),
                                                   effective_config.get('authType', 'none'), effective_config)
            elif node_type == 'delete':
                response_data = self._test_delete_url(full_url, self._setup_request_headers(effective_config),
                                                      effective_config.get('authType', 'none'), effective_config)
            else:
                return self._create_skipped_result(node)

            status_code = response_data.get('status_code')
            if status_code and 200 <= status_code < 300:
                status = 'success'
                success_flag = True
                message = f'{node_type.upper()} request successful - HTTP {status_code}'
            else:
                status = 'error'
                success_flag = False
                message = f'{node_type.upper()} request failed - HTTP {status_code}'

            return {
                'node_id': node['id'],
                'node_type': node_type,
                'status': status,
                'message': message,
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time', 0),
                'headers': response_data.get('headers', {}),
                'success': success_flag
            }

        except Exception as e:
            return self._create_error_result(node, full_url, node_type, str(e))

    def _track_all_connections_from_node(self, node_id, connections, flow_execution_data):
        """Track all connections originating from a node"""
        connections_found = 0
        for conn in connections:
            if conn['source'] == node_id:
                connection_exists = any(
                    existing_conn['source'] == conn['source'] and
                    existing_conn['target'] == conn['target']
                    for existing_conn in flow_execution_data['executed_connections']
                )

                if not connection_exists:
                    connection_data = {
                        'source': conn['source'],
                        'target': conn['target'],
                        'outputType': conn.get('outputType')
                    }
                    flow_execution_data['executed_connections'].append(connection_data)
                    connections_found += 1
                    _logger.info(f'Tracked connection: {conn["source"]} -> {conn["target"]}')
        if connections_found > 0:
            _logger.info(f'Tracked {connections_found} connections from node {node_id}')

    def _evaluate_condition_independently(self, condition_node, node_results_map, connections):
        """
        Evaluate condition node independently using ONLY connected node data
        """

        config = condition_node.get('config', {})
        node_id = condition_node['id']

        try:
            connected_response_data = self._get_connected_previous_response(node_id, connections, node_results_map)

            left_value = self._get_condition_left_operand_connected(config, connected_response_data)
            right_value = config.get('rightOperand', '')
            operator = config.get('operator', 'equals')


            result = self._perform_comparison(left_value, right_value, operator)

            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'success',
                'message': f'Condition evaluated: {result}',
                'condition_result': result,
                'evaluation_details': {
                    'left_operand': config.get('leftOperand'),
                    'operator': operator,
                    'right_operand': right_value,
                    'actual_left_value': left_value,
                    'actual_right_value': right_value,
                    'source_data': config.get('sourceData', 'static'),
                    'data_path': config.get('dataPath', ''),
                    'connected_node_data_used': True if connected_response_data else False
                }
            }

        except Exception as e:
            _logger.error(f' Condition evaluation failed for {node_id}: {str(e)}')
            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'error',
                'message': f'Condition evaluation failed: {str(e)}',
                'condition_result': False,
                'evaluation_details': {
                    'error': str(e),
                    'left_operand': config.get('leftOperand'),
                    'operator': config.get('operator', 'equals'),
                    'right_operand': config.get('rightOperand')
                }
            }

    def _get_connected_previous_response(self, condition_node_id, connections, node_results_map):
        """
        Get response data ONLY from the node connected to this condition node's input
        """

        input_connections = [conn for conn in connections if conn['target'] == condition_node_id]

        if not input_connections:
            _logger.warning(f'No input connection found for condition node: {condition_node_id}')
            return None

        input_connection = input_connections[0]
        source_node_id = input_connection['source']

        if source_node_id in node_results_map:
            source_result = node_results_map[source_node_id]
            if source_result.get('status') == 'success':
                response_data = source_result.get('response_data') or source_result.get('data')
                return response_data
            else:
                _logger.warning(f' Connected node {source_node_id} has status: {source_result.get("status")}')
        else:
            _logger.warning(f' Connected node {source_node_id} not found in results')

        return None

    def _get_next_nodes_with_conditional_logic(self, current_node_id, node_type, node_result, connections,
                                               node_results_map):
        """
        Get next nodes to execute based on conditional logic - COMPLETE REWRITE
        """
        next_nodes = []

        outgoing_connections = [conn for conn in connections if conn['source'] == current_node_id]

        for conn in outgoing_connections:
            _logger.info(f'Connection: {conn["source"]} -> {conn["target"]} (output: {conn.get("outputType")})')

        for conn in outgoing_connections:
            target_node_id = conn['target']
            output_type = conn.get('outputType')

            if node_type == 'condition':
                condition_result = node_result.get('condition_result') if node_result else False

                if (condition_result is True and output_type == 'true') or \
                        (condition_result is False and output_type == 'false') or \
                        (output_type not in ['true', 'false']):
                    next_nodes.append(target_node_id)


            elif node_type in ['start', 'endpoint', 'get', 'post', 'put', 'delete']:
                next_nodes.append(target_node_id)

            else:
                next_nodes.append(target_node_id)

        seen = set()
        unique_next_nodes = []
        for node_id in next_nodes:
            if node_id not in seen:
                seen.add(node_id)
                unique_next_nodes.append(node_id)

        return unique_next_nodes

    def _evaluate_condition_node(self, condition_node, node_results_map):
        """Evaluate a condition node against the workflow results."""
        config = condition_node.get('config', {})

        try:

            previous_responses = [
                r for r in node_results_map.values()
                if r.get('node_type') in ['get', 'post', 'put', 'delete', 'webhook'] and r.get('status') == 'success'
            ]

            data_to_pass = {}
            if previous_responses:
                data_to_pass = previous_responses[-1].get('response_data', {})
                if not data_to_pass:
                    data_to_pass = previous_responses[-1].get('data', {})

            left_value = self._get_condition_left_operand(config, previous_responses)
            right_value = config.get('rightOperand', '')
            operator = config.get('operator', 'equals')

            result = self._perform_comparison(left_value, right_value, operator)

            return {
                'node_id': condition_node['id'],
                'node_type': 'condition',
                'status': 'success',
                'condition_result': result,
                'response_data': data_to_pass,
                'message': f"Result: {result}"
            }
        except Exception as e:
            return {
                'node_id': condition_node['id'],
                'status': 'error',
                'message': f"Condition Error: {e}"
            }



    def _get_condition_left_operand(self, config, previous_responses):
        """
        Retrieves the value for the left side of the comparison.
        Handles both Static input and Connected Node Response.
        """
        source_type = config.get('sourceData', 'static')

        if source_type == 'previous_response':

            path = config.get('leftOperand') or config.get('dataPath')

            if not path:
                return None

            if previous_responses:
                last_response = previous_responses[-1]
                data = last_response.get('response_data') or last_response.get('data') or {}

                return self._extract_json_path_value(data, path)

            return None

        elif source_type == 'static':
            context = {}
            if previous_responses:
                last_data = previous_responses[-1].get('response_data', {}) or previous_responses[-1].get('data', {})
                context['data'] = last_data
                if isinstance(last_data, dict):
                    context.update(last_data)

            raw_val = config.get('leftOperand')

            if raw_val and isinstance(raw_val, str) and '{{' in raw_val:
                return self._substitute_variables(raw_val, context)

            return raw_val

        return None

    def _should_connection_be_active(self, connection, source_result):
        """Determine if a connection should be active based on the source node's result."""
        if not source_result: return False

        if source_result.get('status') != 'success':
            return False

        # Standard Node (GET, ORM, etc) -> Always continue
        if source_result.get('node_type') != 'condition':
            return True

        # Condition Node Logic
        condition_result = source_result.get('condition_result')  # True / False
        output_type = connection.get('outputType')  # 'true' (Green dot) or 'false' (Red dot)

        if output_type == 'true' and condition_result is True:
            return True
        if output_type == 'false' and condition_result is False:
            return True

        return False

    @api.model
    def test_workflow(self, workflow_data):
        """Main entry point for testing a complete workflow."""
        import time

        # 1. Initialize with Trigger Data (Automation / Odoo Events)
        initial_data = workflow_data.get('initial_data') or {}

        # WE INITIALIZE HERE AND DO NOT RESET IT LATER
        node_results_map = {
            'trigger': {
                'status': 'success',
                'response_data': initial_data,
                'node_type': 'trigger'
            }
        }

        # 2. Setup Data Structures
        nodes = workflow_data.get('nodes', [])
        connections = workflow_data.get('connections', [])
        target_node_id = workflow_data.get('target_node_id')

        if not nodes:
            return {'success': False, 'message': "No nodes found"}

        node_map = {n['id']: n for n in nodes}
        adj_list = {n['id']: [] for n in nodes}
        for c in connections:
            if c['source'] in adj_list:
                adj_list[c['source']].append(c)

        # 3. Find Entry Point
        start_node = next((n for n in nodes if n.get('type') == 'start'), None)
        if not start_node:
            all_targets = set(c['target'] for c in connections)
            start_node = next((n for n in nodes if n['id'] not in all_targets), nodes[0])

        # 4. Execution Queue
        queue = [start_node['id']]
        visited = set()
        results = []

        success = True
        endpoint_config = {}
        base_url = ""

        # Global Config lookup
        ep_node = next((n for n in nodes if n.get('type') == 'endpoint'), None)
        if ep_node:
            endpoint_config = ep_node.get('config', {})
            base_url = (endpoint_config.get('baseUrl') or "").strip()

        # --- MAIN LOOP ---
        while queue:
            current_node_id = queue.pop(0)

            if current_node_id in visited:
                continue
            visited.add(current_node_id)

            current_node = node_map.get(current_node_id)
            if not current_node: continue

            # EXECUTE NODE
            step_result = self._execute_node_safe(
                current_node,
                node_results_map,
                connections,
                nodes,
                endpoint_config,
                base_url
            )

            node_results_map[current_node_id] = step_result
            results.append(step_result)

            # Target Node Check (Test Until Here)
            if target_node_id and current_node_id == target_node_id:
                queue = []
                success = step_result.get('success', True)
                break

            # Handle Loop Nodes (Flatten sub-results and mark children visited)
            if current_node.get('type') == 'loop':
                sub_results = step_result.get('sub_results', [])
                results.extend(sub_results)
                for sub in sub_results:
                    s_id = sub.get('node_id')
                    if s_id:
                        node_results_map[s_id] = sub
                        visited.add(s_id)  # Prevents loop children from running again in main queue

            # Stop workflow if a node returns an error
            if step_result.get('status') == 'error':
                success = False
                break

            # FIND NEXT NODES
            outgoing = adj_list.get(current_node_id, [])
            for conn in outgoing:
                target_id = conn['target']
                if self._should_connection_be_active(conn, step_result):
                    queue.append(target_id)

        return {
            'success': success,
            'results': results,
            'message': "Workflow completed" if success else "Workflow stopped on error",
            'node_results': results
        }

    def _execute_node_safe(self, node, node_results_map, connections, all_nodes, endpoint_config, base_url):
        """ Routes execution and ensures UI gets the correct Success Flag """
        node_type = node.get('type')
        node_id = node.get('id')

        result = {}

        # 🛠️ CONTEXT BUILDER (FIXED)
        # We need to construct a clean dictionary of variables for {{ variable }}
        global_context = {}

        for key, val in node_results_map.items():
            # Get the payload
            payload = val.get('response_data') or val.get('data')

            if payload:
                # SPECIAL HANDLING FOR TRIGGER
                # If this is the "trigger" result (from Automation/Cron)
                # It comes in as {'trigger': {'id': 1...}}.
                # We want to merge that directly into root so {{ trigger.id }} works.
                if key == 'trigger' and isinstance(payload, dict):
                    global_context.update(payload)
                else:
                    # Normal nodes: Access via Node ID (e.g. {{ node_123.id }})
                    global_context[key] = payload

        # Add generic helpers
        import datetime
        global_context['datetime'] = datetime.datetime.now()

        try:
            # 1. ORM
            if node_type == 'orm':
                prev_data = self._get_connected_previous_response(node_id, connections, node_results_map)

                # Merge Contexts
                context_data = global_context.copy()
                context_data['previous_data'] = prev_data
                # Allow access to 'data' (synonym for previous_data)
                if prev_data: context_data['data'] = prev_data

                result = self._run_orm_node(node, context_data)

            # 2. CONDITION
            elif node_type == 'condition':
                result = self._evaluate_condition_node(node, node_results_map)

            # 3. API
            elif node_type in ['get', 'post', 'put', 'delete', 'endpoint']:
                result = self._execute_api_node(node, base_url, endpoint_config, context=global_context)

            # 4. LOOP
            elif node_type == 'loop':
                prev_data = self._get_connected_previous_response(node_id, connections, node_results_map)
                loop_res = self._run_loop_node(node, prev_data, all_nodes, connections, endpoint_config, base_url)
                result = {
                    'node_id': node_id,
                    'status': 'success',
                    'message': f"Loop finished ({len(loop_res)} items)",
                    'sub_results': loop_res
                }

            # 5. OTHERS
            else:
                result = {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'success',
                    'message': "Node processed"
                }

        except Exception as e:
            import traceback
            _logger.error(traceback.format_exc())
            result = {'node_id': node_id, 'status': 'error', 'message': str(e)}

        if result.get('status') == 'success':
            result['success'] = True
        else:
            result['success'] = False

        return result
    def _extract_json_path_value(self, data, json_path):
        """
        Extract value from response data using JSON path
        """
        if data is None:
            return None

        if not json_path or json_path == '$' or json_path == '.' or json_path == '':
            return data

        try:
            path_parts = json_path.split('.')
            current = data

            for part in path_parts:
                if part == '$': continue
                if not part: continue  # Skip empty splits

                if current is None:
                    return None

                # Handle Array Index [0]
                if '[' in part and ']' in part:
                    import re
                    match = re.match(r'(\w*)\[(\d+)\]', part)
                    if match:
                        array_name, index_str = match.groups()

                        if array_name:
                            if isinstance(current, dict) and array_name in current:
                                current = current[array_name]
                            else:
                                return None

                        if isinstance(current, list):
                            index = int(index_str)
                            if 0 <= index < len(current):
                                current = current[index]
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                # Handle Dictionary Key
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

            return current

        except Exception as e:
            _logger.error(f'❌ JSON path extraction failed: {json_path} - {str(e)}')
            return None

    def _create_node_results(self, results):
        """Create node results from execution results"""
        node_results = []
        for result in results:
            if isinstance(result, dict):
                # Determine success based on multiple possible keys
                is_success = result.get('success', False)
                if result.get('status') == 'success':
                    is_success = True

                node_results.append({
                    'node_id': result.get('node_id'),
                    'success': is_success,
                    'status': result.get('status', 'unknown'),  # UI often uses 'status'
                    'error': result.get('error'),
                    'message': result.get('message'),
                    'node_type': result.get('node_type'),

                    # ✅ IMPORTANT: PASS THE DATA TO THE FRONTEND
                    'response_data': result.get('response_data') or result.get('data'),
                    'headers': result.get('headers'),
                    'status_code': result.get('status_code'),
                    'response_time': result.get('response_time'),

                    'flow_path': 'executed'
                })
        return node_results

    def _substitute_variables(self, payload, context_data):
        """
        Recursively replaces {{ variable }} with actual values.
        - Handles Brackets: data[0].title -> data.0.title
        - Handles Dots: data.0.title
        - Handles Magic: download(http://...)
        """
        # 1. Recursion for Dicts/Lists
        if isinstance(payload, dict):
            return {k: self._substitute_variables(v, context_data) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [self._substitute_variables(item, context_data) for item in payload]

        # 2. Skip if not string
        if not isinstance(payload, str):
            return payload

        val = payload.strip()

        # --- A. Check for Variable Substitution ---
        if "{{" in val and "}}" in val:
            import re

            def get_val(path, ctx):
                """Resolve a dot-notation path against the context."""
                # 🧼 CLEANUP SYNTAX:
                # Convert "data.[0].title" or "data[0].title" into "data.0.title"
                clean = path.replace('.[', '.').replace('[', '.').replace(']', '').replace('..', '.')
                parts = [p for p in clean.split('.') if p]  # Split and remove empty strings

                curr = ctx
                for part in parts:
                    if curr is None: return None

                    # 1. Dictionary
                    if isinstance(curr, dict):
                        curr = curr.get(part)
                    # 2. Odoo Record
                    elif hasattr(curr, part):
                        curr = getattr(curr, part)
                    # 3. List / Tuple Index
                    elif isinstance(curr, (list, tuple)) and part.isdigit():
                        try:
                            idx = int(part)
                            if 0 <= idx < len(curr):
                                curr = curr[idx]
                            else:
                                return None
                        except:
                            return None
                    else:
                        return None  # Path invalid
                return curr

            # Regex: Matches {{ variable.path }} including brackets
            pattern = r'\{\{\s*([a-zA-Z0-9_\[\]\.]+)\s*\}\}'

            # Strategy 1: Exact Match (Preserves Data Type)
            # Example: "{{ price }}" -> 10.5 (Float)
            exact_match = re.match(f'^{pattern}$', val)
            if exact_match:
                res = get_val(exact_match.group(1), context_data)
                # Update val to the resolved result if found
                # If resolved is a string, we continue to check for 'download()'
                if res is not None:
                    if not isinstance(res, str):
                        return res  # Return Non-string types immediately
                    val = res  # Update local val string

            # Strategy 2: String Interpolation
            # Example: "ID is {{ id }}" -> "ID is 123"
            else:
                def replacer(match):
                    """Replace regex match with resolved variable value."""
                    res = get_val(match.group(1), context_data)
                    return str(res) if res is not None else match.group(0)

                val = re.sub(pattern, replacer, val)

        # --- B. Handle Magic Functions (like Image Download) ---
        if isinstance(val, str) and val.startswith('download(') and val.endswith(')'):
            url = val[9:-1].strip()
            if url.startswith('http'):
                try:
                    import requests
                    import base64
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        return base64.b64encode(response.content).decode('utf-8')
                except Exception as e:
                    _logger.error(f"Image download error: {e}")

        return val

    def _get_variable_value(self, path, context_data):
        """
        Helper to traverse 'loopItem.order_line.id'.
        Supports Dictionaries AND Odoo Recordsets.
        """
        if not path: return None

        parts = path.split('.')
        current = context_data

        for part in parts:
            if current is None:
                return None

            # 1. Handle Dictionary (API Data)
            if isinstance(current, dict):
                current = current.get(part)

            # 2. Handle Odoo Recordset (ORM Data)
            elif hasattr(current, part):
                current = getattr(current, part)

            # 3. Handle List Index (e.g. lines.0.id)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None  # Path broken/invalid

        return current

    def _run_orm_node(self, node, context_data):
        """ Execute Odoo ORM methods with DEBUG LOGS and SAVEPOINT """

        config = node.get('config', {})
        model_name = config.get('model')
        operation = config.get('operation', 'create')

        # 1. Parse JSON Input
        try:
            json_str = config.get('field_values_json', '{}')
            # If empty string, default based on operation
            if not json_str or not json_str.strip():
                if operation in ['search', 'search_read', 'search_count', 'unlink']:
                    json_str = '[]'
                else:
                    json_str = '{}'

            # Standardize quotes helper (Allow Single Quotes -> Double Quotes)
            if "'" in json_str and '"' not in json_str:
                if json_str.strip().startswith('[') or json_str.strip().startswith('{'):
                    try:
                        import ast
                        lit = ast.literal_eval(json_str)
                        json_str = json.dumps(lit)
                    except:
                        pass

            raw_values = json.loads(json_str)
        except Exception as e:
            return {
                'node_id': node['id'],
                'status': 'error',
                'message': f"Invalid JSON: {e}"
            }

        if not model_name or model_name not in self.env:
            return {'node_id': node['id'], 'status': 'error', 'message': f"Model '{model_name}' not found."}

        model = self.env[model_name].sudo()

        # =========================================================
        # 2. PREPARE CONTEXT (CRITICAL FIX: UNWRAP DATA)
        # =========================================================
        safe_context = context_data.copy() if context_data else {}

        raw_payload = safe_context.get('previous_data')
        real_payload = {}


        if raw_payload and isinstance(raw_payload, dict):
            if 'response_data' in raw_payload and isinstance(raw_payload['response_data'], dict):
                real_payload = raw_payload['response_data']
            else:
                real_payload = raw_payload

        if real_payload:
            safe_context['data'] = real_payload
            for k, v in real_payload.items():
                if k not in safe_context:
                    safe_context[k] = v

        elif 'data' not in safe_context:
            safe_context['data'] = safe_context

        for key, value in list(safe_context.items()):
            if isinstance(key, str) and '-' in key:
                safe_key = key.replace('-', '_')
                if safe_key not in safe_context:
                    safe_context[safe_key] = value


        try:
            with self.env.cr.savepoint():
                input_data = self._substitute_variables(raw_values, safe_context)

                raw_record_id = config.get('record_id')

                if isinstance(input_data, dict) and (input_data.get('id') or input_data.get('record_id')):
                    raw_record_id = input_data.get('id') or input_data.get('record_id')

                final_record_id = None
                if raw_record_id:
                    if isinstance(raw_record_id, str) and '{{' in raw_record_id:
                        final_record_id = self._substitute_variables(raw_record_id, safe_context)
                    else:
                        final_record_id = raw_record_id

                    try:
                        if isinstance(final_record_id, list) and len(final_record_id) > 0:
                            final_record_id = int(final_record_id[0])
                        elif final_record_id is not None:
                            final_record_id = int(float(final_record_id))
                    except (ValueError, TypeError):
                        pass

                result_data = {}
                message = ""


                if operation == 'search':
                    if isinstance(input_data, list):
                        domain = input_data
                        limit = int(config.get('limit', 10))
                        fields_to_read = None
                    else:
                        domain = input_data.get('domain', [])
                        limit = int(input_data.get('limit', config.get('limit', 10)))
                        fields_to_read = input_data.get('fields')

                    if not fields_to_read:
                        fields_to_read = config.get('fields')

                    if isinstance(fields_to_read, str) and fields_to_read.strip():
                        fields_to_read = [f.strip() for f in fields_to_read.split(',') if f.strip()]

                    if fields_to_read:
                        result_data = model.search_read(domain, fields=fields_to_read, limit=limit)
                        message = f"Found {len(result_data)} records (with fields)."
                    else:
                        records = model.search(domain, limit=limit)
                        result_data = [{'id': r.id, 'name': r.display_name} for r in records]
                        message = f"Found {len(result_data)} records."


                elif operation == 'search_read':
                    if isinstance(input_data, list):
                        domain = input_data
                        limit = int(config.get('limit', 0)) or None
                        order = None
                        fields = None
                    else:
                        domain = input_data.get('domain', [])
                        fields = input_data.get('fields', [])
                        limit = int(input_data.get('limit', config.get('limit', 0))) or None
                        order = input_data.get('order', '')

                    if not fields:
                        fields_str = config.get('fields')
                        if fields_str and isinstance(fields_str, str):
                            fields = [f.strip() for f in fields_str.split(',') if f.strip()]

                    records = model.search_read(domain, fields=fields if fields else None, limit=limit, order=order)
                    result_data = records
                    message = f"Fetched {len(records)} records."


                elif operation == 'search_count':
                    if isinstance(input_data, list):
                        domain = input_data
                    else:
                        domain = input_data.get('domain', [])
                    count = model.search_count(domain)
                    result_data = {'count': count}
                    message = f"Count result: {count}"


                elif operation == 'read':
                    if not final_record_id:
                        raise Exception(f"Record ID missing for READ. Input: {raw_record_id}")

                    # FIX: Check if input_data is dict before .get()
                    fields = None
                    if isinstance(input_data, dict):
                        fields = input_data.get('fields')

                    if not fields:
                        fields = config.get('fields')

                    if isinstance(fields, str) and fields.strip():
                        fields = [f.strip() for f in fields.split(',')]

                    if not fields: fields = ['display_name']

                    ids_to_read = [final_record_id] if isinstance(final_record_id, int) else final_record_id

                    result_data = model.browse(ids_to_read).read(fields)
                    message = f"Read {len(result_data)} records."


                elif operation == 'create':
                    if isinstance(input_data, list):
                        raise Exception(f"Create expects Dictionary, got List: {input_data}")

                    vals = {k: v for k, v in input_data.items()
                            if k not in ['id', 'record_id', 'domain', 'limit', 'fields']}

                    record = model.create(vals)
                    result_data = {'id': record.id, 'name': record.display_name}
                    message = f"Created {model_name} (ID: {record.id})"


                elif operation == 'write':
                    if not final_record_id:
                        raise Exception("Record ID required for WRITE")

                    if isinstance(input_data, list):
                        raise Exception(f"Update expects Dictionary, got List: {input_data}")

                    clean_vals = {k: v for k, v in input_data.items() if
                                  k not in ['id', 'record_id', 'domain', 'limit', 'fields']}

                    model.browse(int(final_record_id)).write(clean_vals)
                    result_data = {'id': int(final_record_id), 'status': 'updated'}
                    message = f"Updated {model_name} (ID: {final_record_id})"


                elif operation == 'unlink':
                    if final_record_id:
                        model.browse(int(final_record_id)).unlink()
                        result_data = {'id': int(final_record_id), 'status': 'deleted'}
                        message = f"Deleted {model_name} (ID: {final_record_id})"
                    elif isinstance(input_data, list):
                        if not input_data: raise Exception("Delete by Domain requires non-empty domain.")
                        records_to_delete = model.search(input_data)
                        count = len(records_to_delete)
                        if count > 0:
                            records_to_delete.unlink()
                            result_data = {'count': count, 'status': 'deleted_batch'}
                            message = f"Deleted {count} records."
                        else:
                            result_data = {'count': 0, 'status': 'no_match'}
                            message = "No records found to delete."
                    else:
                        raise Exception("For Delete, provide Record ID OR JSON Search Domain.")

                return {
                    'node_id': node['id'],
                    'node_type': 'orm',
                    'status': 'success',
                    'success': True,
                    'message': message,
                    'response_data': result_data
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'node_id': node['id'],
                'node_type': 'orm',
                'status': 'error',
                'success': False,
                'message': f"ORM Error: {str(e)}"
            }


    def _run_loop_node(self, loop_node, previous_data, nodes, connections, endpoint_config, base_url):
        """Execute a loop node, iterating over a collection of items."""

        config = loop_node.get("config", {})
        collection_path = config.get("collectionPath", "$")

        items_to_loop = []
        if isinstance(previous_data, dict) and 'records' in previous_data:
            items_to_loop = previous_data['records']
        elif isinstance(previous_data, list):
            items_to_loop = previous_data
        else:
            items_to_loop = self._extract_json_path_value(previous_data, collection_path)

        if not isinstance(items_to_loop, list):
            return [{'node_id': loop_node['id'], 'status': 'error', 'message': "Not a list"}]

        results = []
        items_to_process = items_to_loop[:50]
        start_nodes_ids = [c["target"] for c in connections if c["source"] == loop_node["id"]]

        node_success_tracker = {}

        def execute_branch(current_node_id, current_context, depth=0):
            """Recursively execute a branch of the workflow."""
            if depth > 20: return

            node = next((n for n in nodes if n["id"] == current_node_id), None)
            if not node: return

            node_type = node.get('type')
            node_result = None

            try:
                if node_type == 'orm':
                    node_result = self._run_orm_node(node, current_context)
                elif node_type == 'condition':
                    node_result = self._evaluate_condition_in_loop(node, current_context)
                elif node_type in ['get', 'post', 'put', 'delete']:
                    node_result = self._execute_api_node(node, base_url, endpoint_config,context=current_context)

                if node_result:
                    iter_info = f"[Iter {current_context.get('iter_index')}]"
                    node_result['message'] = f"{iter_info} {node_result.get('message', '')}"
                    results.append(node_result)

                    if node_type == 'condition':
                        is_true = node_result.get('condition_result', False)
                        if is_true:
                            node_success_tracker[current_node_id] = True
                        elif current_node_id not in node_success_tracker:
                            node_success_tracker[current_node_id] = False

                    if node_result.get('status') == 'error':
                        return

                    next_context = current_context.copy()
                    payload = node_result.get('response_data') or node_result.get('data')
                    if payload:
                        next_context['previous_data'] = payload
                        if isinstance(payload, dict):
                            next_context.update(payload)

                    outgoing = [c for c in connections if c['source'] == current_node_id]
                    next_targets = []

                    if node.get('type') == 'condition':
                        res = node_result.get('condition_result')
                        for c in outgoing:
                            o = c.get('outputType')
                            if (res is True and o == 'true') or (res is False and o == 'false'):
                                next_targets.append(c['target'])
                    else:
                        next_targets = [c['target'] for c in outgoing]

                    for t in next_targets:
                        execute_branch(t, next_context, depth + 1)

            except Exception as e:
                _logger.error(f"❌ Loop Error: {e}")

        for index, item in enumerate(items_to_process):
            ctx = {
                'loopItem': item,
                'item': item,
                'iter_index': index + 1,
                'previous_data': previous_data
            }
            for start_id in start_nodes_ids:
                execute_branch(start_id, ctx)

        for node_id, was_ever_true in node_success_tracker.items():
            if was_ever_true:
                results.append({
                    'node_id': node_id,
                    'node_type': 'condition',
                    'status': 'success',
                    'success': True,
                    'condition_result': True,
                    'message': "Loop Completed (At least one iteration was True)",
                    'evaluation_details': {
                        'branch_taken': 'TRUE',
                        'note': 'Visual Summary'
                    }
                })

        return results

    def _evaluate_condition_in_loop(self, condition_node, context):
        """
        Evaluate Condition inside a loop.
        """
        node_id = condition_node.get('id')
        config = condition_node.get('config', {})

        # 1. Get Configuration
        left_raw = config.get('leftOperand', '')
        operator = config.get('operator', 'equals')
        right_raw = config.get('rightOperand', '')

        left_val = None
        left_val = self._get_nested_value(context, left_raw)
        if left_val is None and 'item' in context:
            left_val = self._get_nested_value(context['item'], left_raw)
        if left_val is None:
            left_val = self._substitute_variables(left_raw, context)

        right_val = self._substitute_variables(right_raw, context)

        is_true = self._evaluate_condition(left_val, operator, right_val)
        return {
            'node_id': node_id,
            'node_type': 'condition',
            'status': 'success',
            'success': True,
            'condition_result': is_true,
            'message': f"Checked: {left_val} {operator} {right_val} = {is_true}",
            'response_data': context.get('item', {}),
            'evaluation_details': {
                'branch_taken': 'TRUE' if is_true else 'FALSE',
                'left': str(left_val),
                'right': str(right_val)
            }
        }

    def _get_nested_value(self, data, path):
        """
        Retrieves value from nested dictionary/object using dot notation.
        """
        if not path or not isinstance(path, str):
            return None

        if isinstance(data, dict) and path in data:
            return data[path]

        keys = path.split('.')
        current_value = data

        try:
            for key in keys:
                if isinstance(current_value, dict):
                    current_value = current_value.get(key)
                elif hasattr(current_value, key):
                    current_value = getattr(current_value, key)
                elif isinstance(current_value, list) and key.isdigit():
                    idx = int(key)
                    if 0 <= idx < len(current_value):
                        current_value = current_value[idx]
                    else:
                        return None
                else:
                    return None  # Path broken

                if current_value is None:
                    return None

            return current_value
        except Exception as e:
            return None

    def _evaluate_condition(self, left_val, operator, right_val):
        """ Robust comparison that handles String vs Number issues """


        try:
            if isinstance(left_val, (int, float)) and isinstance(right_val, str):
                right_val = float(right_val)

            elif isinstance(left_val, str) and isinstance(right_val, str):
                if left_val.replace('.', '', 1).isdigit() and right_val.replace('.', '', 1).isdigit():
                    left_val = float(left_val)
                    right_val = float(right_val)
        except ValueError:
            pass

        if operator == 'equals':
            return left_val == right_val
        elif operator == 'not_equals':
            return left_val != right_val
        elif operator == 'greater_than':
            try:
                return float(left_val) > float(right_val)
            except:
                return str(left_val) > str(right_val)
        elif operator == 'less_than':
            try:
                return float(left_val) < float(right_val)
            except:
                return str(left_val) < str(right_val)
        elif operator == 'contains':
            return str(right_val) in str(left_val)
        elif operator == 'exists':
            return bool(left_val)

        return False

    def _execute_simple_independent(self, nodes, connections, endpoint_config, base_url):
        """
        Execute workflow and track data flow.
        Prevents double-execution of nodes that ran inside a loop.
        """
        results = []
        executed_nodes = set()
        node_results_map = {}

        flow_execution_data = {'flow_results': [], 'executed_connections': []}

        execution_order = self._build_execution_order_with_branching(nodes, connections, node_results_map)


        for node_id in execution_order:
            if node_id in executed_nodes:
                continue

            current_node = next((n for n in nodes if n.get('id') == node_id), None)
            if not current_node: continue

            # Mark as executed immediately
            executed_nodes.add(node_id)

            node_type = current_node.get('type')
            result = None

            # === LOOP NODE HANDLING ===
            if node_type == "loop":
                # Get previous data
                prev_result = self._get_connected_previous_response(node_id, connections, node_results_map)

                # Run Loop
                loop_results = self._run_loop_node(
                    current_node, prev_result, nodes, connections, endpoint_config, base_url
                )
                results.extend(loop_results)

                # Map the FIRST result to the map (just so downstream nodes have something reference)
                if loop_results:
                    node_results_map[node_id] = loop_results[0]


                for res in loop_results:
                    child_id = res.get('node_id')
                    if child_id:
                        executed_nodes.add(child_id)

            # === CONDITION NODE HANDLING ===
            elif node_type == 'condition':
                result = self._evaluate_condition_with_branching(current_node, node_results_map, connections)
                results.append(result)
                node_results_map[node_id] = result

            # === ORM NODE HANDLING ===
            elif node_type == 'orm':
                prev_result = self._get_connected_previous_response(node_id, connections, node_results_map)
                context_data = {'previous_data': prev_result}

                for n_id, res in node_results_map.items():
                    context_data[n_id] = res.get('response_data')

                result = self._run_orm_node(current_node, context_data)
                results.append(result)
                node_results_map[node_id] = result

            # === STANDARD NODES ===
            else:
                result = self._execute_non_condition_node(current_node, endpoint_config, base_url)
                results.append(result)
                node_results_map[node_id] = result

            if node_type != 'loop':
                self._track_executed_connections(node_id, connections, flow_execution_data)

        return results, flow_execution_data

    def _track_executed_connections(self, node_id, connections, flow_data):
        """
        Helper to mark connections as executed for the UI (draws green lines)
        """
        # Find connections starting from this node
        outgoing = [c for c in connections if c['source'] == node_id]

        for conn in outgoing:
            # check if already tracked to avoid duplicates
            exists = any(
                c['source'] == conn['source'] and c['target'] == conn['target']
                for c in flow_data['executed_connections']
            )

            if not exists:
                flow_data['executed_connections'].append({
                    'source': conn['source'],
                    'target': conn['target'],
                    'outputType': conn.get('outputType')
                })

    def _execute_non_condition_node(self, node, endpoint_config, base_url):
        """
        Execute non-condition nodes (API endpoints, start, end)
        """
        node_id = node.get('id')
        node_type = node.get('type')
        config = node.get('config', {})

        try:
            if node_type == 'endpoint':
                return self._test_endpoint_node_complete(node, config)

            elif node_type in ['get', 'post', 'put', 'delete']:
                path = config.get('url', '')
                full_url = self._join_url(base_url, path)

                if node_type == 'get':
                    return self._test_get_node_simple(node, full_url, config, endpoint_config)
                elif node_type == 'post':
                    return self._test_post_node_simple(node, full_url, config, endpoint_config)
                elif node_type == 'put':
                    return self._test_put_node_simple(node, full_url, config, endpoint_config)
                elif node_type == 'delete':
                    return self._test_delete_node_simple(node, full_url, config, endpoint_config)

            elif node_type in ['start', 'end']:
                return {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'success',
                    'message': f'{node_type.capitalize()} node processed',
                    'success': True
                }


            elif node_type == 'loop':
                mode = config.get('mode', 'fixed')
                max_iterations = int(config.get('maxIterations', 1))
                if mode == "fixed":
                    return {

                        'node_id': node_id,
                        'node_type': 'loop',
                        'status': 'success',
                        'message': f'Loop executed {max_iterations} times',
                        'loop_iterations': list(range(max_iterations)),
                        'success': True
                    }
                return {
                    'node_id': node_id,
                    'node_type': 'loop',
                    'status': 'error',
                    'message': f'Loop mode \"{mode}\" not implemented',
                    'success': False
                }



        except Exception as e:
            _logger.error(f'❌ Node execution failed: {node_id} - {str(e)}')
            return {
                'node_id': node_id,
                'node_type': node_type,
                'status': 'error',
                'message': f'Execution failed: {str(e)}',
                'success': False,
                'error': str(e)
            }

    def _test_get_node_simple(self, node, full_url, config, endpoint_config):
        """Simple GET node test"""
        try:
            effective_config = config.copy()
            auth_type = config.get('authType', 'none')

            if auth_type == 'none' and endpoint_config:
                headers = {}
                effective_config = {**endpoint_config, **config}

            headers = self._setup_request_headers(effective_config)
            response_data = self._test_url(full_url, headers, auth_type, effective_config)

            is_success = response_data.get('success', False)
            status_code = response_data.get('status_code')

            return {
                'node_id': node['id'],
                'node_type': 'get',
                'status': 'success' if is_success else 'error',
                'message': f'GET request {"successful" if is_success else "failed"} - HTTP {status_code}',
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time', 0),
                'success': is_success
            }
        except Exception as e:
            return self._create_error_result(node, full_url, 'get', str(e))

    def _test_post_node_simple(self, node, full_url, config, endpoint_config):
        """Simple POST node test"""
        try:
            effective_config = config.copy()
            auth_type = config.get('authType', 'none')

            if auth_type == 'none' and endpoint_config:
                effective_config = {**endpoint_config, **config}

            headers = self._setup_request_headers(effective_config)
            response_data = self._test_post_url(full_url, headers, auth_type, effective_config)

            is_success = response_data.get('success', False)
            status_code = response_data.get('status_code')

            return {
                'node_id': node['id'],
                'node_type': 'post',
                'status': 'success' if is_success else 'error',
                'message': f'POST request {"successful" if is_success else "failed"} - HTTP {status_code}',
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time', 0),
                'success': is_success
            }
        except Exception as e:
            return self._create_error_result(node, full_url, 'post', str(e))

    def _test_put_node(self, node, full_url, config, auth_type, endpoint_config=None):
        """Test a PUT node"""
        try:
            if auth_type == 'none' and endpoint_config:
                auth_type = endpoint_config.get('authType', 'none')
                config = {**endpoint_config, **config}

            headers = self._setup_request_headers(config)

            # Call fixed tester
            response_data = self._test_put_url(full_url, headers, auth_type, config)

            # Safe Status Check
            is_success = response_data.get('success', False)
            status_code = response_data.get('status_code')

            code_display = status_code if status_code else "N/A"
            msg_type = "successful" if is_success else "failed"

            return {
                'node_id': node['id'],
                'node_type': 'put',
                'status': 'success' if is_success else 'error',
                'message': f'PUT request {msg_type} - HTTP {code_display}',
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {})
            }
        except Exception as e:
            return self._create_error_result(node, full_url, 'put', str(e))

    def _test_delete_node(self, node, full_url, config, auth_type, endpoint_config=None):
        """Test a DELETE node with correct Status Check"""
        try:
            if auth_type == 'none' and endpoint_config:
                auth_type = endpoint_config.get('authType', 'none')
                config = {**endpoint_config, **config}

            headers = self._setup_request_headers(config)

            response_data = self._test_delete_url(full_url, headers, auth_type, config)

            is_success = response_data.get('success', False)
            status_code = response_data.get('status_code')

            status = 'success' if is_success else 'error'

            code_display = status_code if status_code else "N/A"
            msg_type = "successful" if is_success else "failed"
            message = f'DELETE request {msg_type} - HTTP {code_display}'

            return {
                'node_id': node['id'],
                'node_type': 'delete',
                'status': status,
                'message': message,
                'url': full_url,
                'response_data': response_data.get('data'),
                'status_code': status_code,
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {})
            }
        except Exception as e:
            return self._create_error_result(node, full_url, 'delete', str(e))

    def _get_condition_left_operand_connected(self, condition_config, connected_response_data):
        """
        Get left operand value for condition evaluation using ONLY connected node data.
        Updated to support {{data[0].price}} in independent tests.
        """
        source_data = condition_config.get('sourceData', 'static')

        # Case 1: Dropdown Selection
        if source_data == 'previous_response' and connected_response_data:
            data_path = condition_config.get('dataPath', '')
            if data_path:
                return self._extract_json_path_value(connected_response_data, data_path)

        # Case 2: Manual Input (Static) with {{ data... }}
        else:
            val = condition_config.get('leftOperand', '')

            if isinstance(val, str) and val.strip().startswith('{{') and val.strip().endswith('}}'):
                if connected_response_data:
                    clean_ref = val.strip()[2:-2].strip()

                    if clean_ref.startswith('data'):
                        json_path = clean_ref[4:]
                        if json_path.startswith('.'):
                            json_path = json_path[1:]
                        extracted = self._extract_json_path_value(connected_response_data, json_path)
                        return extracted
                else:
                    _logger.info(" Syntax detected but NO connected data found.")

            return val

    def _execute_branch_from_node(self, current_node_id, nodes, connections, endpoint_config,
                                  base_url, executed_nodes, node_results_map, results, flow_execution_data):
        """
        Recursively execute a branch starting from a specific node
        """
        if current_node_id in executed_nodes:
            return

        executed_nodes.add(current_node_id)
        current_node = next((n for n in nodes if n.get('id') == current_node_id), None)

        if not current_node:
            _logger.error(f'❌ Node not found: {current_node_id}')
            return

        node_type = current_node.get('type')

        node_result = self._execute_single_node_with_branching(
            current_node, endpoint_config, base_url, node_results_map
        )

        if node_result:
            results.append(node_result)
            node_results_map[current_node_id] = node_result

            self._track_connection_for_branch(current_node_id, connections, flow_execution_data)

        next_nodes = self._get_next_nodes_with_proper_branching(
            current_node_id, node_type, node_result, connections, node_results_map
        )


        for next_node_id in next_nodes:
            self._execute_branch_from_node(
                next_node_id, nodes, connections, endpoint_config,
                base_url, executed_nodes, node_results_map, results, flow_execution_data
            )

    def _get_next_nodes_with_proper_branching(self, current_node_id, node_type, node_result, connections,
                                              node_results_map):
        """
        Get next nodes based on proper branching logic
        """

        next_nodes = []
        outgoing_connections = [conn for conn in connections if conn['source'] == current_node_id]


        for conn in outgoing_connections:
            target_node_id = conn['target']
            output_type = conn.get('outputType')

            if node_type == 'condition':
                condition_result = node_result.get('condition_result') if node_result else False

                if output_type == 'true' and condition_result is True:
                    next_nodes.append(target_node_id)
                elif output_type == 'false' and condition_result is False:
                    next_nodes.append(target_node_id)
                elif output_type not in ['true', 'false']:
                    next_nodes.append(target_node_id)
            else:
                next_nodes.append(target_node_id)

        seen = set()
        unique_next_nodes = []
        for node_id in next_nodes:
            if node_id not in seen:
                seen.add(node_id)
                unique_next_nodes.append(node_id)

        return unique_next_nodes

    def _execute_single_node_with_branching(self, node, endpoint_config, base_url, node_results_map):
        """
        Execute a single node with branching support
        """
        node_id = node.get('id')
        node_type = node.get('type')

        try:
            if node_type == 'condition':
                return self._evaluate_condition_with_proper_branching(node, node_results_map)
            elif node_type in ['get', 'post', 'put', 'delete', 'endpoint']:
                return self._execute_api_node(node, base_url, endpoint_config)
            elif node_type in ['start', 'end']:
                return {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'success',
                    'message': f'{node_type.capitalize()} node processed'
                }
            else:
                return {
                    'node_id': node_id,
                    'node_type': node_type,
                    'status': 'skipped',
                    'message': f'Unknown node type: {node_type}'
                }
        except Exception as e:
            _logger.error(f'❌ Node execution failed: {node_id} - {str(e)}')
            return {
                'node_id': node_id,
                'node_type': node_type,
                'status': 'error',
                'message': f'Execution failed: {str(e)}',
                'error': str(e)
            }

    def _evaluate_condition_with_proper_branching(self, condition_node, node_results_map):
        """
        Evaluate condition with proper connection-aware data extraction for branching
        """
        config = condition_node.get('config', {})
        node_id = condition_node['id']

        try:
            connected_response_data = self._get_connected_previous_response(node_id, node_results_map)

            left_value = self._get_condition_left_operand_connected(config, connected_response_data)
            right_value = config.get('rightOperand', '')
            operator = config.get('operator', 'equals')


            result = self._perform_comparison(left_value, right_value, operator)

            evaluation_details = {
                'left_operand': config.get('leftOperand'),
                'operator': operator,
                'right_operand': right_value,
                'actual_left_value': left_value,
                'actual_right_value': right_value,
                'source_data': config.get('sourceData', 'static'),
                'data_path': config.get('dataPath', ''),
                'connected_node_data_used': True if connected_response_data else False,
                'branch_taken': 'TRUE' if result else 'FALSE'
            }


            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'success',
                'message': f'Condition evaluated: {result} -> {evaluation_details["branch_taken"]} branch',
                'condition_result': result,
                'evaluation_details': evaluation_details
            }

        except Exception as e:
            _logger.error(f'❌ Condition evaluation failed for {node_id}: {str(e)}')
            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'error',
                'message': f'Condition evaluation failed: {str(e)}',
                'condition_result': False,
                'evaluation_details': {
                    'error': str(e),
                    'branch_taken': 'FALSE (error)'
                }
            }

    def _track_connection_for_branch(self, node_id, connections, flow_execution_data):
        """
        Track connections that were actually followed in branching execution
        """
        outgoing_connections = [conn for conn in connections if conn['source'] == node_id]

        for conn in outgoing_connections:
            if not any(c['source'] == conn['source'] and c['target'] == conn['target']
                       for c in flow_execution_data['executed_connections']):
                connection_data = {
                    'source': conn['source'],
                    'target': conn['target'],
                    'outputType': conn.get('outputType'),
                    'branch_executed': True
                }
                flow_execution_data['executed_connections'].append(connection_data)


    def _build_execution_order_with_branching(self, nodes, connections, node_results_map):
        """
        Build execution order that respects conditional branching
        """
        node_ids = [node['id'] for node in nodes if isinstance(node, dict) and 'id' in node]

        has_incoming = set(conn['target'] for conn in connections)
        start_nodes = [node_id for node_id in node_ids if node_id not in has_incoming]

        if not start_nodes:
            start_nodes = [n['id'] for n in nodes if n.get('type') == 'start']
        if not start_nodes and node_ids:
            start_nodes = [node_ids[0]]


        execution_order = []
        visited = set()
        queue = collections.deque(start_nodes)

        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue

            visited.add(node_id)
            execution_order.append(node_id)

            next_nodes = self._get_next_nodes_with_branching(node_id, connections, node_results_map)

            for next_id in next_nodes:
                if next_id not in visited:
                    queue.append(next_id)

        for node_id in node_ids:
            if node_id not in visited:
                execution_order.append(node_id)

        return execution_order

    def _get_next_nodes_with_branching(self, current_node_id, connections, node_results_map):
        """
        Get next nodes based on conditional branching logic
        """


        next_nodes = []
        outgoing_connections = [conn for conn in connections if conn['source'] == current_node_id]

        current_node_result = node_results_map.get(current_node_id, {})
        current_node_type = current_node_result.get('node_type', 'unknown')

        for conn in outgoing_connections:
            target_node_id = conn['target']
            output_type = conn.get('outputType')

            if current_node_type == 'condition':
                condition_result = current_node_result.get('condition_result')

                if output_type == 'true' and condition_result is True:
                    next_nodes.append(target_node_id)
                elif output_type == 'false' and condition_result is False:
                    next_nodes.append(target_node_id)
                elif output_type not in ['true', 'false']:
                    next_nodes.append(target_node_id)
            else:
                next_nodes.append(target_node_id)

        seen = set()
        unique_next_nodes = []
        for node_id in next_nodes:
            if node_id not in seen:
                seen.add(node_id)
                unique_next_nodes.append(node_id)

        return unique_next_nodes

    def _evaluate_condition_with_branching(self, condition_node, node_results_map, connections):
        """
        Main entry point for processing a condition node.
        """

        config = condition_node.get('config', {})
        node_id = condition_node['id']

        try:
            connected_data = self._get_connected_previous_response(node_id, connections, node_results_map)

            context_data = {'previous_data': connected_data}

            left_val = self._get_condition_left_operand(config, connected_data)

            raw_right = config.get('rightOperand', '')
            right_val = self._substitute_variables(raw_right, context_data)

            operator = config.get('operator', 'equals')

            result = self._perform_comparison(left_val, right_val, operator)

            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'success',
                'message': f'Result: {result}',
                'condition_result': result,
                'evaluation_details': {
                    'left': left_val,
                    'right': right_val,
                    'operator': operator,
                    'branch': 'TRUE' if result else 'FALSE'
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'node_id': node_id,
                'node_type': 'condition',
                'status': 'error',
                'message': f'Error: {str(e)}',
                'condition_result': False
            }
    def _track_condition_branches(self, condition_node_id, condition_result, connections, flow_execution_data):
        """
        Track which branches were taken by condition nodes
        """
        outgoing_connections = [conn for conn in connections if conn['source'] == condition_node_id]

        for conn in outgoing_connections:
            output_type = conn.get('outputType')
            target_node_id = conn['target']

            branch_taken = False
            if output_type == 'true' and condition_result is True:
                branch_taken = True
            elif output_type == 'false' and condition_result is False:
                branch_taken = True
            elif output_type not in ['true', 'false']:
                branch_taken = True

            if branch_taken:
                connection_data = {
                    'source': conn['source'],
                    'target': conn['target'],
                    'outputType': output_type,
                    'condition_branch_taken': True,
                    'branch_type': output_type
                }

                if not any(c['source'] == connection_data['source'] and c['target'] == connection_data['target']
                           for c in flow_execution_data['executed_connections']):
                    flow_execution_data['executed_connections'].append(connection_data)


    def _auto_convert(self, value):
        """
        Smartly converts strings to Int/Float/Bool/None for comparison.
        """
        if value is None:
            return None

        if isinstance(value, (int, float, bool, list, dict)):
            return value

        val_str = str(value).strip()

        if val_str.lower() == 'true': return True
        if val_str.lower() == 'false': return False
        if val_str.lower() == 'none' or val_str.lower() == 'null': return None

        try:
            return int(val_str)
        except (ValueError, TypeError):
            pass

        try:
            return float(val_str)
        except (ValueError, TypeError):
            pass

        return value
