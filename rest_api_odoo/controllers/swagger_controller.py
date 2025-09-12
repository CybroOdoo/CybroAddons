# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#    Modified by: [Tu nombre] - Agregado Swagger/OpenAPI Documentation
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
from datetime import datetime
from odoo import http
from odoo.http import request


class SwaggerController(http.Controller):
    """Controlador para generar documentación Swagger/OpenAPI de la REST API"""

    @http.route(
        ["/api/v1/docs", "/api/docs"], type="http", auth="none", methods=["GET"]
    )
    def swagger_ui(self, **kwargs):
        """Muestra la interfaz de Swagger UI"""
        base_url = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "http://localhost:8069")
        )

        swagger_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Odoo REST API - Swagger Documentation</title>
                <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
                <style>
                    html {{
                        box-sizing: border-box;
                        overflow: -moz-scrollbars-vertical;
                        overflow-y: scroll;
                    }}
                    *, *:before, *:after {{
                        box-sizing: inherit;
                    }}
                    body {{
                        margin:0;
                        background: #fafafa;
                        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                    }}
                    #swagger-ui {{
                        max-width: 1200px;
                        margin: 0 auto;
                    }}
                    .topbar {{
                        background-color: #89bf04 !important;
                    }}
                    .topbar .download-url-wrapper .download-url-button {{
                        background-color: #7aa30a !important;
                        border-color: #7aa30a !important;
                    }}
                    .swagger-ui .info .title {{
                        color: #89bf04;
                    }}
                </style>
            </head>
            <body>
                <div id="swagger-ui"></div>

                <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
                <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
                <script>
                    window.onload = function() {{
                        const ui = SwaggerUIBundle({{
                            url: '{base_url}/api/v1/openapi.json',
                            dom_id: '#swagger-ui',
                            deepLinking: true,
                            presets: [
                                SwaggerUIBundle.presets.apis,
                                SwaggerUIStandalonePreset
                            ],
                            plugins: [
                                SwaggerUIBundle.plugins.DownloadUrl
                            ],
                            layout: "StandaloneLayout",
                            validatorUrl: null,
                            tryItOutEnabled: true,
                            supportedSubmitMethods: ['get', 'post', 'put', 'delete'],
                            onComplete: function() {{
                                console.log("Swagger UI loaded successfully");
                            }},
                            requestInterceptor: function(req) {{
                                // Agregar headers por defecto si no están presentes
                                if (!req.headers['Content-Type'] && req.method !== 'GET') {{
                                    req.headers['Content-Type'] = 'application/json';
                                }}
                                return req;
                            }}
                        }});

                        window.ui = ui;
                    }}
                </script>
            </body>
            </html>
            """
        return request.make_response(
            swagger_html, headers=[("Content-Type", "text/html; charset=utf-8")]
        )

    @http.route(["/api/v1/openapi.json"], type="http", auth="none", methods=["GET"])
    def openapi_spec(self, **kwargs):
        """Genera la especificación OpenAPI/Swagger en formato JSON"""

        base_url = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "http://localhost:8069")
        )
        db_name = request.env.cr.dbname

        # Obtener información de modelos configurados
        api_configs = (
            request.env["connection.api"].sudo().search([("active", "=", True)])
        )

        # Estructura base de OpenAPI 3.0
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Odoo REST API",
                "description": f"""
                    ## Odoo REST API Documentation

                    Esta es la documentación interactiva de la REST API para Odoo. La API permite realizar operaciones CRUD en los modelos configurados de Odoo.

                    ### Autenticación

                    La API utiliza autenticación basada en API Key. Para obtener una API Key:

                    1. **Primer paso - Autenticarse:**
                    ```bash
                    curl -X POST {base_url}/api/v1/auth \\
                        -H "Content-Type: application/json" \\
                        -d '{{"username": "tu_usuario", "password": "tu_contraseña", "database": "{db_name}"}}'
                    2. Usar la API Key en las requests:
                        - Agregar header: X-API-Key: tu_api_key_aqui
                        - O usar header: api-key: tu_api_key_aqui

                        Formatos de Respuesta
                        Todas las respuestas siguen un formato estandarizado:

                        Respuesta exitosa:
                        {{
                            "success": true,
                            "count": 10,
                            "data": [...]
                        }}
                        Respuesta de error:
                        {{
                            "error": true,
                            "message": "Descripción del error",
                            "status_code": 400,
                            "error_code": "ERROR_CODE"
                        }}
                        Campos Especiales
                    Fechas: Se devuelven en formato ISO 8601 (YYYY-MM-DDTHH:MM:SS)

                    Archivos binarios: Se codifican en Base64

                    Relaciones Many2one: Se devuelven como [id, "display_name"]

                    Relaciones One2many/Many2many: Se devuelven como arrays de IDs

                    Modelos Disponibles
                    {self._get_available_models_description()}
                    """,
                "version": "1.0.0",
                "contact": {"name": "API Support", "email": "support@example.com"},
                "license": {
                    "name": "LGPL-3",
                    "url": "https://www.gnu.org/licenses/lgpl-3.0.html",
                },
            },
            "servers": [
                {"url": f"{base_url}/api/v1", "description": "Production server"}
            ],
            "security": [{"ApiKeyAuth": []}],
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                        "description": "API Key obtenida del endpoint de autenticación",
                    }
                },
                "schemas": {
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "boolean", "example": True},
                            "message": {
                                "type": "string",
                                "example": "Descripción del error",
                            },
                            "status_code": {"type": "integer", "example": 400},
                            "error_code": {"type": "string", "example": "ERROR_CODE"},
                        },
                    },
                    "AuthRequest": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {"type": "string", "example": "admin"},
                            "password": {"type": "string", "example": "admin"},
                            "database": {"type": "string", "example": f"{db_name}"},
                        },
                    },
                    "AuthResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {
                                "type": "string",
                                "example": "Autenticación exitosa",
                            },
                            "data": {
                                "type": "object",
                                "properties": {
                                    "user_id": {"type": "integer", "example": 2},
                                    "username": {"type": "string", "example": "admin"},
                                    "name": {
                                        "type": "string",
                                        "example": "Administrator",
                                    },
                                    "api_key": {
                                        "type": "string",
                                        "example": "abcd1234...",
                                    },
                                    "database": {
                                        "type": "string",
                                        "example": f"{db_name}",
                                    },
                                },
                            },
                        },
                    },
                    "SuccessResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "count": {"type": "integer", "example": 10},
                            "data": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                },
                "responses": {
                    "UnauthorizedError": {
                        "description": "API Key missing or invalid",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                    "NotFoundError": {
                        "description": "Resource not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                    "ValidationError": {
                        "description": "Invalid request data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            },
            "paths": self._generate_paths(api_configs),
            "tags": self._generate_tags(api_configs),
        }

        return request.make_response(
            json.dumps(openapi_spec, indent=2),
            headers=[("Content-Type", "application/json; charset=utf-8")],
        )


    def _get_available_models_description(self):
        """Genera descripción de modelos disponibles"""
        api_configs = request.env["connection.api"].sudo().search([("active", "=", True)])
        if not api_configs:
            return "No hay modelos configurados actualmente."

        description = "Los siguientes modelos están disponibles:\n\n"
        for config in api_configs:
            methods = []
            if config.is_get:
                methods.append("GET")
            if config.is_post:
                methods.append("POST")
            if config.is_put:
                methods.append("PUT")
            if config.is_delete:
                methods.append("DELETE")

            description += f"- **{config.model_id.name}** (`{config.model_id.model}`) - Métodos: {', '.join(methods)}\n"

        return description


    def _generate_tags(self, api_configs):
        """Genera tags para agrupar endpoints"""
        tags = [
            {
                "name": "Authentication",
                "description": "Endpoints para autenticación y gestión de API keys",
            },
            {
                "name": "System",
                "description": "Endpoints del sistema (información de modelos disponibles)",
            },
        ]

        for config in api_configs:
            tags.append(
                {
                    "name": config.model_id.model,
                    "description": f"Operaciones CRUD para el modelo {config.model_id.name}",
                }
            )

        return tags


    def _generate_paths(self, api_configs):
        """Genera todos los paths/endpoints de la API"""
        paths = {}

        # Endpoint de autenticación
        paths["/auth"] = {
            "post": {
                "tags": ["Authentication"],
                "summary": "Authenticate user and get API key",
                "description": "Autentica un usuario y devuelve una API key para usar en las demás requests",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AuthRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Autenticación exitosa",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AuthResponse"}
                            }
                        },
                    },
                    "401": {"$ref": "#/components/responses/UnauthorizedError"},
                },
                "security": [],
            }
        }

        # Endpoint de modelos disponibles
        paths["/models"] = {
            "get": {
                "tags": ["System"],
                "summary": "List available models",
                "description": "Lista todos los modelos disponibles en la API con sus métodos permitidos",
                "responses": {
                    "200": {
                        "description": "Lista de modelos disponibles",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                            }
                        },
                    },
                    "401": {"$ref": "#/components/responses/UnauthorizedError"},
                },
            }
        }

        # Generar endpoints para cada modelo configurado
        for config in api_configs:
            model_name = config.model_id.model
            model_display_name = config.model_id.name

            # Path para operaciones de colección (GET all, POST)
            collection_path = f"/{model_name}"
            paths[collection_path] = {}

            # Path para operaciones de item específico (GET one, PUT, DELETE)
            item_path = f"/{model_name}/{{id}}"
            paths[item_path] = {}

            # Obtener campos del modelo
            model_fields = self._get_model_fields_info(model_name)

            # GET - Obtener todos los registros
            if config.is_get:
                paths[collection_path]["get"] = {
                    "tags": [model_name],
                    "summary": f"Get all {model_display_name} records",
                    "description": f"Obtiene todos los registros del modelo {model_display_name}",
                    "parameters": [
                        {
                            "name": "fields",
                            "in": "query",
                            "description": "Campos específicos a retornar (separados por comas)",
                            "schema": {"type": "string", "example": "id,name,email"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Lista de registros",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            },
                        },
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }

                # GET - Obtener registro específico
                paths[item_path]["get"] = {
                    "tags": [model_name],
                    "summary": f"Get specific {model_display_name} record",
                    "description": f"Obtiene un registro específico del modelo {model_display_name}",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "description": "ID del registro",
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Registro encontrado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            },
                        },
                        "404": {"$ref": "#/components/responses/NotFoundError"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }

            # POST - Crear registro
            if config.is_post:
                paths[collection_path]["post"] = {
                    "tags": [model_name],
                    "summary": f"Create new {model_display_name} record",
                    "description": f"Crea un nuevo registro en el modelo {model_display_name}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["values"],
                                    "properties": {
                                        "values": {
                                            "type": "object",
                                            "description": "Datos del registro a crear",
                                            "properties": model_fields,
                                        },
                                        "fields": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Campos a retornar en la respuesta",
                                        },
                                    },
                                },
                                "example": self._get_model_example_data(
                                    model_name, "create"
                                ),
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Registro creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/ValidationError"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }

            # PUT - Actualizar registro
            if config.is_put:
                paths[item_path]["put"] = {
                    "tags": [model_name],
                    "summary": f"Update {model_display_name} record",
                    "description": f"Actualiza un registro existente del modelo {model_display_name}",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "description": "ID del registro a actualizar",
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["values"],
                                    "properties": {
                                        "values": {
                                            "type": "object",
                                            "description": "Datos a actualizar",
                                            "properties": model_fields,
                                        },
                                        "fields": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Campos a retornar en la respuesta",
                                        },
                                    },
                                },
                                "example": self._get_model_example_data(
                                    model_name, "update"
                                ),
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Registro actualizado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            },
                        },
                        "404": {"$ref": "#/components/responses/NotFoundError"},
                        "400": {"$ref": "#/components/responses/ValidationError"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }

            # DELETE - Eliminar registro
            if config.is_delete:
                paths[item_path]["delete"] = {
                    "tags": [model_name],
                    "summary": f"Delete {model_display_name} record",
                    "description": f"Elimina un registro del modelo {model_display_name}",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "description": "ID del registro a eliminar",
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Registro eliminado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean", "example": True},
                                            "message": {
                                                "type": "string",
                                                "example": "Registro eliminado exitosamente",
                                            },
                                            "deleted_record": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "display_name": {"type": "string"},
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        "404": {"$ref": "#/components/responses/NotFoundError"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }

        return paths

    def _get_model_fields_info(self, model_name):
        """Obtiene información de los campos de un modelo para la documentación"""
        try:
            model = request.env[model_name].sudo()
            fields_info = {}

            # Campos comunes que suelen existir
            common_fields = {
                "id": {
                    "type": "integer",
                    "description": "ID único del registro",
                    "readOnly": True,
                },
                "name": {"type": "string", "description": "Nombre"},
                "display_name": {
                    "type": "string",
                    "description": "Nombre para mostrar",
                    "readOnly": True,
                },
                "create_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Fecha de creación",
                    "readOnly": True,
                },
                "write_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Fecha de última modificación",
                    "readOnly": True,
                },
                "active": {
                    "type": "boolean",
                    "description": "Indica si el registro está activo",
                },
            }

            # Agregar campos comunes que existan en el modelo
            for field_name, field_info in common_fields.items():
                if hasattr(model, field_name):
                    fields_info[field_name] = field_info

            return fields_info

        except Exception:
            # Si hay error, retornar estructura básica
            return {
                "id": {"type": "integer", "description": "ID único del registro"},
                "display_name": {
                    "type": "string",
                    "description": "Nombre para mostrar",
                },
            }

    def _get_model_example_data(self, model_name, operation):
        """Genera ejemplos de datos para cada modelo"""
        examples = {
            "res.partner": {
                "create": {
                    "values": {
                        "name": "Nuevo Cliente",
                        "email": "cliente@ejemplo.com",
                        "phone": "+34123456789",
                        "is_company": False,
                    },
                    "fields": ["id", "name", "email", "phone"],
                },
                "update": {
                    "values": {"phone": "+34987654321", "street": "Calle Nueva 123"},
                    "fields": ["id", "name", "phone", "street"],
                },
            },
            "product.product": {
                "create": {
                    "values": {
                        "name": "Nuevo Producto",
                        "list_price": 99.99,
                        "default_code": "PROD001",
                    },
                    "fields": ["id", "name", "list_price", "default_code"],
                },
                "update": {
                    "values": {
                        "list_price": 89.99,
                        "description": "Descripción actualizada",
                    },
                    "fields": ["id", "name", "list_price", "description"],
                },
            },
        }

        # Retornar ejemplo específico o genérico
        return examples.get(
            model_name,
            {
                "create": {
                    "values": {"name": "Nuevo Registro"},
                    "fields": ["id", "name", "display_name"],
                },
                "update": {
                    "values": {"name": "Registro Actualizado"},
                    "fields": ["id", "name", "display_name"],
                },
            },
        ).get(operation, {})
