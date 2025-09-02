# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
import logging
import base64
from odoo import http
from odoo.http import request
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    """This is a controller which is used to generate responses based on the
    api requests"""

    def auth_api_key(self, api_key):
        """This function is used to authenticate the api-key when sending a
        request"""
        user_id = request.env['res.users'].sudo().search([('api_key', '=', api_key)])
        if api_key is not None and user_id:
             response = True
        elif not user_id:
            response = ('<html><body><h2>Invalid <i>API Key</i> '
                        '!</h2></body></html>')
        else:
            response = ("<html><body><h2>No <i>API Key</i> Provided "
                        "!</h2></body></html>")
        return response

    def generate_response(self, method, model, rec_id, request_params=None):
        """This function is used to generate the response based on the type
        of request and the parameters given"""
        option = request.env['connection.api'].search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model

        # Handle data based on method
        if method == 'GET':
            # For GET requests, check both JSON body and query parameters
            data = request_params or {}
            fields = []

            # First, try to get fields from JSON body
            try:
                if request.httprequest.data:
                    json_data = json.loads(request.httprequest.data)
                    if 'fields' in json_data:
                        fields = json_data['fields']
            except json.JSONDecodeError:
                pass  # If JSON is invalid, continue with query params

            # If no fields from JSON, try query parameters
            if not fields:
                fields_param = data.get('fields', '')
                if fields_param:
                    fields = [field.strip() for field in fields_param.split(',')]

            # If still no fields, use defaults based on record type
            if not fields:
                if rec_id != 0:
                    # For specific record, get all fields
                    fields = None  # This will get all available fields
                else:
                    # For all records, use minimal fields
                    fields = ['id', 'display_name']
        elif method != 'DELETE':
            # For POST/PUT requests, parse JSON from body
            try:
                if request.httprequest.data:
                    data = json.loads(request.httprequest.data)
                else:
                    data = {}
            except json.JSONDecodeError:
                return ("<html><body><h2>Invalid JSON Data"
                        "</h2></body></html>")
        else:
            # DELETE method
            data = {}
            fields = []

        # Extract fields for POST/PUT methods
        if method in ['POST', 'PUT'] and data:
            fields = []
            if 'fields' in data:
                for field in data['fields']:
                    fields.append(field)

        if not fields and method != 'DELETE' and method != 'GET':
            return ("<html><body><h2>No fields selected for the model"
                    "</h2></body></html>")
        if not option:
            return ("<html><body><h2>No Record Created for the model"
                    "</h2></body></html>")
        try:
            if method == 'GET':
                if not option.is_get:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    datas = []
                    if rec_id != 0:
                        # For specific record
                        search_fields = fields if fields is not None else []
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', rec_id)],
                            fields=search_fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                                elif isinstance(value, bytes):
                                    # Convert bytes to base64 string for JSON serialization
                                    import base64
                                    record[key] = base64.b64encode(value).decode('utf-8')
                                elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                    # Handle other non-serializable iterables
                                    try:
                                        record[key] = list(value) if value else []
                                    except:
                                        record[key] = str(value)
                                elif isinstance(value, bytes):
                                    # Convert bytes to base64 string for JSON serialization
                                    import base64
                                    record[key] = base64.b64encode(value).decode('utf-8')
                                elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                    # Handle other non-serializable iterables
                                    try:
                                        record[key] = list(value) if value else []
                                    except:
                                        record[key] = str(value)
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
                    else:
                        # For all records
                        search_fields = fields if fields is not None else ['id', 'display_name']
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[],
                            fields=search_fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
        except Exception as e:
            _logger.error(f"Error in GET method: {str(e)}")
            return ("<html><body><h2>Error processing request"
                    "</h2></body></html>")

        if method == 'POST':
            if not option.is_post:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                try:
                    datas = []
                    new_resource = request.env[str(model_name)].create(
                        data['values'])
                    partner_records = request.env[
                        str(model_name)].search_read(
                        domain=[('id', '=', new_resource.id)],
                        fields=fields
                    )
                    for record in partner_records:
                        for key, value in record.items():
                            if isinstance(value, (datetime, date)):
                                record[key] = value.isoformat()
                            elif isinstance(value, bytes):
                                # Convert bytes to base64 string for JSON serialization
                                import base64
                                record[key] = base64.b64encode(value).decode('utf-8')
                            elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                # Handle other non-serializable iterables
                                try:
                                    record[key] = list(value) if value else []
                                except:
                                    record[key] = str(value)
                            elif isinstance(value, bytes):
                                # Convert bytes to base64 string for JSON serialization
                                import base64
                                record[key] = base64.b64encode(value).decode('utf-8')
                            elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                # Handle other non-serializable iterables
                                try:
                                    record[key] = list(value) if value else []
                                except:
                                    record[key] = str(value)
                    new_data = json.dumps({'New resource': partner_records, })
                    datas.append(new_data)
                    return request.make_response(data=datas)
                except Exception as e:
                    _logger.error(f"Error in POST method: {str(e)}")
                    return ("<html><body><h2>Invalid JSON Data"
                            "</h2></body></html>")

        if method == 'PUT':
            if not option.is_put:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:
                        try:
                            datas = []
                            resource.write(data['values'])
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=fields
                            )
                            for record in partner_records:
                                for key, value in record.items():
                                    if isinstance(value, (datetime, date)):
                                        record[key] = value.isoformat()
                                    elif isinstance(value, bytes):
                                        # Convert bytes to base64 string for JSON serialization
                                        import base64
                                        record[key] = base64.b64encode(value).decode('utf-8')
                                    elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                        # Handle other non-serializable iterables
                                        try:
                                            record[key] = list(value) if value else []
                                        except:
                                            record[key] = str(value)
                                    elif isinstance(value, bytes):
                                        # Convert bytes to base64 string for JSON serialization
                                        import base64
                                        record[key] = base64.b64encode(value).decode('utf-8')
                                    elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                                        # Handle other non-serializable iterables
                                        try:
                                            record[key] = list(value) if value else []
                                        except:
                                            record[key] = str(value)
                            new_data = json.dumps(
                                {'Updated resource': partner_records,
                                 })
                            datas.append(new_data)
                            return request.make_response(data=datas)

                        except Exception as e:
                            _logger.error(f"Error in PUT method: {str(e)}")
                            return ("<html><body><h2>Invalid JSON Data "
                                    "!</h2></body></html>")

        if method == 'DELETE':
            if not option.is_delete:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:
                        records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', resource.id)],
                            fields=['id', 'display_name']
                        )
                        remove = json.dumps(
                            {"Resource deleted": records,
                             })
                        resource.unlink()
                        return request.make_response(data=remove)

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """This controller will be called when sending a request to the
        specified url, and it will authenticate the api-key and then will
        generate the result"""
        http_method = request.httprequest.method

        api_key = request.httprequest.headers.get('api-key')
        auth_api = self.auth_api_key(api_key)
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        credential = {'login': username, 'password': password, 'type': 'password'}
        request.session.authenticate(request.session.db, credential)
        model_id = request.env['ir.model'].search(
            [('model', '=', model)])
        if not model_id:
            return ("<html><body><h3>Invalid model, check spelling or maybe "
                    "the related "
                    "module is not installed"
                    "</h3></body></html>")

        if auth_api == True:
            if not kw.get('Id'):
                rec_id = 0
            else:
                rec_id = int(kw.get('Id'))
            # Pass the query parameters for GET requests
            result = self.generate_response(http_method, model_id.id, rec_id, kw)
            return result
        else:
            return auth_api

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self, **kw):
        """This is the controller which initializes the api transaction by
        generating the api-key for specific user and database"""
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            request.session.update(http.get_default_session(), db=db)
            credential = {'login': username, 'password': password,
                          'type': 'password'}

            auth = request.session.authenticate(db, credential)
            user = request.env['res.users'].browse(auth['uid'])
            api_key = request.env.user.generate_api(username)
            datas = json.dumps({"Status": "auth successful",
                                "User": user.name,
                                "api-key": api_key})
            return request.make_response(data=datas)
        except Exception as e:
            _logger.error(f"Error in authentication: {str(e)}")
            return ("<html><body><h2>wrong login credentials"
                    "</h2></body></html>")
