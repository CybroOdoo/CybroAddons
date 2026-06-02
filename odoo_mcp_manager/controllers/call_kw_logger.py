# -*- coding: utf-8 -*-
import json
import logging
import time
import traceback as tb_module
from odoo import api, http
from odoo.http import request
from odoo.addons.web.controllers.dataset import DataSet as _BaseDataSet

_logger = logging.getLogger(__name__)

# If the user-agent contains any of these strings, it's a browser — skip logging.
_BROWSER_MARKERS = ('mozilla', 'applewebkit', 'gecko', 'chrome', 'safari', 'firefox')


def _is_external_client() -> bool:
    """Return True when the request does not appear to originate from a browser."""
    ua = request.httprequest.headers.get('User-Agent', '').lower()
    return not any(m in ua for m in _BROWSER_MARKERS)
try:
    class AiLoggedDataSet(_BaseDataSet):
        """Subclass of Odoo's DataSet controller that writes ai.tool.log records for RPC calls."""
        @http.route(
            ['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'],
            type='json', auth='user',
            readonly=_BaseDataSet._call_kw_readonly,
        )
        def call_kw(self, model: str, method: str, args, kwargs, path=None):
            """
            Wrap the standard call_kw handler with execution logging for external clients.
            Browser sessions and ai.tool.execute calls pass through unlogged.
            """
            if not _is_external_client():
                return super().call_kw(model, method, args, kwargs, path=path)

            if model == 'ai.tool' and method == 'execute':
                return super().call_kw(model, method, args, kwargs, path=path)

            label = f'{model}.{method}'
            log_vals = {
                'source': 'rpc',
                'call_label': label,
                'user_id': request.env.user.id,
                'input_params': json.dumps(
                    {'model': model, 'method': method, 'args': args, 'kwargs': kwargs},
                    default=str,
                )[:3000],
                'status': 'success',
            }

            start = time.perf_counter()
            try:
                result = super().call_kw(model, method, args, kwargs, path=path)
                elapsed = round((time.perf_counter() - start) * 1000, 2)
                log_vals.update({
                    'execution_time_ms': elapsed,
                    'result_preview': str(result)[:500],
                })
                return result
            except Exception as exc:
                elapsed = round((time.perf_counter() - start) * 1000, 2)
                log_vals.update({
                    'status': 'error',
                    'execution_time_ms': elapsed,
                    'error_message': str(exc),
                    'error_traceback': tb_module.format_exc(),
                })
                raise
            finally:
                try:
                    with request.env.registry.cursor() as new_cr:
                        new_env = api.Environment(new_cr, request.env.uid, {})
                        new_env['ai.tool.log'].sudo().create(log_vals)
                except Exception:
                    _logger.exception('AiLog: failed to write RPC log for %s', label)

except ImportError:
    _logger.warning(
        'odoo_mcp_manager: could not import DataSet — '
        'call_kw logging for external clients is disabled'
    )
