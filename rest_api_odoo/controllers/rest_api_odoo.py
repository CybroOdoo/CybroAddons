# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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

from datetime import datetime
from odoo import http, models
from odoo.http import request, Response
from ast import literal_eval

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """This model is used to authenticate the api-key when sending a request"""
    _inherit = "ir.http"

    @classmethod
    def _auth_method_rest_api(cls):
        """This function is used to authenticate the api-key when sending a
        request"""

        try:
            api_key = request.httprequest.headers.get("Authorization").lstrip("Bearer ")
            if not api_key:
                raise PermissionError("Invalid API key provided.")

            user_id = request.env["res.users.apikeys"]._check_credentials(
                scope="rpc", key=api_key
            )
            request.update_env(user_id)
        except Exception as e:
            _logger.error(e)
            return Response(
                json.dumps({"message": e.args[0]}),
                status=401,
                content_type="application/json",
            )


class RestApi(http.Controller):
    """This is a controller which is used to generate responses based on the
    api requests"""

    def simplest_type(self, input):
        """Try cast input into native Python class, otherwise return as string"""
        try:
            return literal_eval(input)
        except Exception:
            # Handle lowercase booleans
            if input == "true":
                return True
            if input == "false":
                return False
            return input

    def sanitize_records(self, records):
        """Sanitize records for response"""
        for record in records:
            for key, value in record.items():
                # Manually convert datetime fields to string format
                if isinstance(value, datetime):
                    record[key] = value.isoformat()
        return records

    def generate_response(self, method, **query):
        """This function is used to generate the response based on the type
        of request and the parameters given"""
        try:
            model = query.pop("model")
            option = request.env["connection.api"].search(
                [("model_id", "=", model)], limit=1
            )
            model_name = option.model_id.model
            model_display_name = option.model_id.name

            try:
                data = json.loads(request.httprequest.data)
            except Exception:
                data = {}

            fields = []
            if data:
                for field in data["fields"]:
                    fields.append(field)

            # Return records' ID by default if not specified
            if not fields:
                fields.append("id")

            # Get all model's fields if wildcard is used
            if "*" in fields:
                fields = []
                record_fields = request.env[str(model_name)].fields_get(
                    [], attributes=["type"]
                )
                for field, value in record_fields.items():
                    value_type = value.get("type")
                    if not (value_type == "binary"):
                        fields.append(field)
            if not option:
                raise NotImplementedError("No Record Created for the model. ")
            if method == "GET":
                if not option.is_get:
                    raise NameError()
                limit = 0
                if query.get("limit"):
                    limit = int(str(query.get("limit")))
                offset = 0
                if query.get("offset"):
                    offset = int(str(query.get("offset")))

                domains = []
                for key, value in query.items():
                    if not (key == "limit" or key == "offset"):
                        domains.append((key, "=", self.simplest_type(value)))
                partner_records = request.env[str(model_name)].search_read(
                    domains, fields, limit=limit, offset=offset
                )

                return Response(
                    json.dumps({"records": self.sanitize_records(partner_records)}),
                    content_type="application/json",
                )
            if method == "POST":
                if not option.is_post:
                    raise NotImplementedError()
                if not data or "values" not in data:
                    raise ValueError("No Data Provided")

                data = json.loads(request.httprequest.data)
                new_resource = request.env[str(model_name)].create(data["values"])
                partner_records = request.env[str(model_name)].search_read(
                    [("id", "=", new_resource.id)], fields
                )
                return Response(
                    json.dumps({"new_record": self.sanitize_records(partner_records)}),
                    status=201,
                    content_type="application/json",
                )
            if method == "PUT":
                if not option.is_put:
                    raise NotImplementedError()

                if "id" not in query:
                    raise ValueError("No ID Provided")
                if not data or "values" not in data:
                    raise ValueError("No Data Provided")

                resource_id = str(query.get("id"))
                resource = request.env[str(model_name)].browse(int(resource_id))
                if not resource.exists():
                    raise ValueError("Resource not found")

                data = json.loads(request.httprequest.data)
                resource.write(data["values"])
                partner_records = request.env[str(model_name)].search_read(
                    [("id", "=", resource.id)], fields
                )
                return Response(
                    json.dumps(
                        {"updated_record": self.sanitize_records(partner_records)}
                    ),
                    content_type="application/json",
                )
            if method == "DELETE":
                if not option.is_delete:
                    raise NotImplementedError()

                if "id" not in query:
                    raise ValueError("No ID Provided")

                resource_id = str(query.get("id"))
                resource = request.env[str(model_name)].browse(int(resource_id))
                if not resource.exists():
                    raise ValueError("Resource not found")

                partner_records = request.env[str(model_name)].search_read(
                    [("id", "=", resource.id)], fields
                )
                resource.unlink()
                return Response(
                    json.dumps(
                        {
                            "message": "Resource deleted",
                            "data": self.sanitize_records(partner_records),
                        }
                    ),
                    status=202,
                    content_type="application/json",
                )

            # If not using any method above, simply return an error
            raise NotImplementedError()
        except ValueError as e:
            return Response(
                json.dumps({"message": e.args[0]}),
                status=403,
                content_type="application/json",
            )
        except NotImplementedError as e:
            return Response(
                json.dumps(
                    {
                        "message": f"Method not allowed. {e.args[0]}Please contact your admininstrator to enable {method} method for {model_display_name or 'this'} record."
                    }
                ),
                status=405,
                content_type="application/json",
            )
        except Exception as e:
            _logger.error(e)
            return Response(
                json.dumps({"message": f"Internal server error. {e.args[0]}"}),
                status=500,
                content_type="application/json",
            )

    @http.route(
        ["/send_request"],
        type="http",
        auth="rest_api",
        methods=["GET", "POST", "PUT", "DELETE"],
        csrf=False,
    )
    def fetch_data(self, **kw):
        """This controller will be called when sending a request to the
        specified url, and it will authenticate the api-key and then will
        generate the result"""

        http_method = request.httprequest.method
        model = kw.pop("model")
        model_id = request.env["ir.model"].search([("model", "=", model)])
        if not model_id:
            return Response(
                json.dumps(
                    {
                        "message": "Invalid model, check spelling or maybe the related module is not installed"
                    }
                ),
                status=403,
                content_type="application/json",
            )

        return self.generate_response(http_method, model=model_id.id, **kw)