# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
import time

import requests

from odoo import api, models
from odoo.exceptions import UserError

from .ai_chat_voice import CHAT_COMPLETIONS_ENDPOINT, MODELS_ENDPOINT

_logger = logging.getLogger(__name__)

# the models of OpenRouter writing text, listed once an hour: (time read, models)
REASONING_MODELS_CACHE_SECONDS = 3600
_REASONING_MODELS_CACHE = {}
MAX_REASONING_TOKENS = 2000


def get_reasoning_models():
    """ The models of OpenRouter that can replace Odoo's AI service: those reading and
    writing text, cheapest first, as ``(id, label)``. Read from OpenRouter once an
    hour; an empty list when it can not be reached. """
    read_at, reasoning_models = _REASONING_MODELS_CACHE.get('models', (0, None))
    if reasoning_models is not None and time.time() - read_at < REASONING_MODELS_CACHE_SECONDS:
        return reasoning_models
    try:
        response = requests.get(MODELS_ENDPOINT, timeout=10)
        response.raise_for_status()
        data = response.json().get('data') or []
    except (requests.RequestException, ValueError) as error:
        _logger.info("AI Chat Pro: the models of OpenRouter could not be read: %s", error)
        return reasoning_models or []
    found = []
    for model in data:
        architecture = model.get('architecture') or {}
        pricing = model.get('pricing') or {}
        # batch models answer later, through another API: no use while the user waits
        if model['id'].endswith(':batch'):
            continue
        try:
            # per million tokens; negative for routers, whose price depends on the model they pick
            prompt_price = float(pricing.get('prompt') or 0) * 1e6
            completion_price = float(pricing.get('completion') or 0) * 1e6
        except (TypeError, ValueError):
            continue
        if (
            'text' not in (architecture.get('input_modalities') or [])
            or 'text' not in (architecture.get('output_modalities') or [])
            or prompt_price < 0 or completion_price < 0
        ):
            continue
        name = model.get('name') or model['id']
        if not prompt_price and not completion_price:
            label = name if 'free' in name.lower() else f"{name} (free)"
        else:
            label = f"{name} (${prompt_price:.2f} / ${completion_price:.2f} per M input / output tokens)"
        found.append((prompt_price + completion_price, model['id'], label))
    reasoning_models = [(model_id, label) for _price, model_id, label in sorted(found)]
    _REASONING_MODELS_CACHE['models'] = (time.time(), reasoning_models)
    return reasoning_models


def get_reasoning_model(env):
    """ The model of OpenRouter replacing Odoo's AI service: only when that is enabled in
    the settings and a model is chosen, else ``False`` (Odoo's AI service answers). """
    IrConfigParameter = env['ir.config_parameter'].sudo()
    if not IrConfigParameter.get_bool('ai_chat_pro.reasoning_openrouter'):
        return False
    model_id = IrConfigParameter.get_str('ai_chat_pro.reasoning_model').strip()
    return model_id if '/' in model_id else False


class AiChatAssistant(models.AbstractModel):
    """ The text written by AI (analyses, values of records to create, charts, report
    summaries): by Odoo's AI service, or by a model of OpenRouter chosen in the settings. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _text_chat(self, prompt, usage=None):
        """ The answer to a prompt, by the model of OpenRouter chosen in the settings,
        else by Odoo's AI service (OLG).

        :param dict usage: the usage of the question, the tokens and cost of OpenRouter
            are added to
        """
        if ai_model := get_reasoning_model(self.env):
            return self._openrouter_chat(prompt, ai_model, usage)
        answer = self._olg_chat(prompt)
        if usage is not None:
            # shown with the answer, beside the decision model
            usage['used_olg'] = True
        return answer

    @api.model
    def _openrouter_chat(self, prompt, ai_model, usage=None):
        """ Ask a model of OpenRouter, with the key of the assistant. """
        # counted apart: the decision model was not called, the sources of answers stay as they are
        call_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        data = self._openrouter_post(CHAT_COMPLETIONS_ENDPOINT, {
            'model': ai_model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,
            'max_tokens': MAX_REASONING_TOKENS,
            'usage': {'include': True},
            'user': str(self.env.uid),
        }, call_usage)
        tokens = data.get('usage') or {}
        if usage is not None:
            # shown with the answer, in place of Odoo's AI service
            usage['text_model'] = ai_model
            usage['prompt_tokens'] += int(tokens.get('prompt_tokens') or 0)
            usage['completion_tokens'] += int(tokens.get('completion_tokens') or 0)
            usage['cost'] += float(tokens.get('cost') or 0.0)
        choices = data.get('choices') or [{}]
        content = (choices[0].get('message') or {}).get('content') or ''
        if isinstance(content, list):
            # some providers answer content parts
            content = ' '.join(part.get('text') or '' for part in content if isinstance(part, dict))
        if not content.strip():
            raise UserError(self.env._("The model %(model)s gave no answer", model=ai_model))
        return content
