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

import base64
import io
import logging
import re

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.pdf import PdfReader

from .ai_chat_assistant import _keywords
from .ai_chat_voice import CHAT_COMPLETIONS_ENDPOINT

_logger = logging.getLogger(__name__)

# documents a question can come with: PDFs, and pictures of documents (scans, photos)
DOCUMENT_TYPES = {
    'pdf': 'application/pdf',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
}
# the model of OpenRouter reading scans and pictures: it reads PDFs and images
DOCUMENT_MODEL = 'google/gemini-2.5-flash-lite'
# a PDF with less text than this is a scan: read by the model
MIN_PDF_TEXT = 40
MAX_PDF_PAGES = 10
# the text of a document given to the AI, at most
MAX_DOCUMENT_TEXT = 6000
MAX_DOCUMENT_TOKENS = 4000
READ_PROMPT = (
    "Transcribe all the text of this business document (an invoice, an order, a quotation...), as it is written: "
    "its parties and addresses, numbers, dates, references, every line of its tables (one line per row, cells "
    "separated by \" | \") and its totals. Reply with the text only, no comment."
)


def get_document_type(name):
    """ The mimetype of a document, from its file name; ``None`` for other files. """
    return DOCUMENT_TYPES.get((name or '').rpartition('.')[2].lower())


class AiChatAssistant(models.AbstractModel):
    """ Records created from a document: "create a vendor bill from this PDF". The
    text of the document is read (by Odoo for PDFs holding text, by a model of
    OpenRouter for scans and pictures), then the record is drafted from it as from a
    request written in the chat: the user checks and confirms the draft. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _read_document(self, attachment, usage):
        """ The text of a document: the text of a PDF, else what a model reading
        documents transcribes of it. """
        attachment.check_access('read')
        mimetype = get_document_type(attachment.name)
        text = ''
        if mimetype == 'application/pdf':
            text = _get_pdf_text(attachment.raw)
        if len(text.strip()) < MIN_PDF_TEXT:
            text = self._transcribe_document(attachment, mimetype, usage)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n', text).strip()
        if not text:
            raise UserError(self.env._("No text could be read in \"%s\".", attachment.name))
        return text[:MAX_DOCUMENT_TEXT]

    @api.model
    def _transcribe_document(self, attachment, mimetype, usage):
        """ The text of a scan or a picture, read by a model of OpenRouter. """
        if not self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.openrouter_api_key'):
            raise UserError(self.env._(
                "\"%s\" holds no text (a scan or a picture): reading it needs the OpenRouter API key, in the "
                "settings.", attachment.name,
            ))
        data = base64.b64encode(attachment.raw).decode()
        if mimetype == 'application/pdf':
            content = {'type': 'file', 'file': {'filename': attachment.name,
                                                'file_data': f"data:application/pdf;base64,{data}"}}
        else:
            content = {'type': 'image_url', 'image_url': {'url': f"data:{mimetype};base64,{data}"}}
        call_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        answer = self._openrouter_post(CHAT_COMPLETIONS_ENDPOINT, {
            'model': DOCUMENT_MODEL,
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': READ_PROMPT}, content]}],
            'temperature': 0,
            'max_tokens': MAX_DOCUMENT_TOKENS,
            'usage': {'include': True},
            'user': str(self.env.uid),
        }, call_usage)
        tokens = answer.get('usage') or {}
        usage['prompt_tokens'] += int(tokens.get('prompt_tokens') or 0)
        usage['completion_tokens'] += int(tokens.get('completion_tokens') or 0)
        usage['cost'] += float(tokens.get('cost') or 0.0)
        usage.setdefault('text_model', DOCUMENT_MODEL)
        text = ((answer.get('choices') or [{}])[0].get('message') or {}).get('content') or ''
        if isinstance(text, list):
            text = ' '.join(part.get('text') or '' for part in text if isinstance(part, dict))
        return text

    @api.model
    def _choose_document_target(self, question, text, usage):
        """ The kind of record a document creates, and the menu it is created from, chosen
        by the AI from the request and the document: an invoice sent to the company is a
        vendor bill, one it sends is a customer invoice. """
        words = self._get_question_keywords(question) | _keywords(text[:500])
        found = [c for c in self._find_candidates(words) if self._can_create(c['model'])][:4]
        # the kind of record the request names, as the agent read it
        target = self._get_intent().get('target') or ''
        named = self._choose_create_model(question, target, usage) if _keywords(target) else None
        if named:
            # the record the request names is the one created ("create a sales order" from a purchase order
            # a customer sent): only its menus are offered
            found = [named] + [c for c in found if c['model'] == named['model'] and c is not named]
        if not found:
            return None
        candidates = self._get_import_menu_options(found)
        options = {}
        for index, candidate in enumerate(candidates):
            defaults = ", ".join(f"{key.removeprefix('default_')}={value}"
                                 for key, value in self._get_import_context(candidate).items())
            options[f"option_{index}"] = (
                f"{candidate['label']} [{candidate['model']}]"
                + (f" (menu {candidate['path']})" if candidate.get('path') else " (no menu)")
                + (f", creating with {defaults}" if defaults else '')
            )
        company = self.env.company.name
        answer = self._ask_json(
            f"A user of Odoo, the business software, at the company \"{company}\", sends a document with a request. "
            "Choose which record the request creates from it, among the options: a bill or invoice the company "
            "receives from a supplier is a vendor bill, one the company sends to its customer is a customer invoice; "
            "an order the company receives from a customer is a sales order, one it sends to a supplier a purchase "
            "order.\nReply with ONLY minified JSON, no text: {\"option\":\"option_N\"}\n"
            f"Request: {question}\nDocument (start):\n{text[:1500]}\nOptions:\n"
            + "\n".join(f"- {key}: {value}" for key, value in options.items()), usage,
        )
        key = answer.get('option')
        return candidates[int(key.removeprefix('option_'))] if key in options else (named or candidates[0])

    @api.model
    def _draft_from_document(self, question, attachment, usage):
        """ The draft of the record a request creates from a document. """
        text = self._read_document(attachment, usage)
        candidate = self._choose_document_target(question, text, usage)
        if not candidate:
            return {'content': self.env._(
                "Which record should I create from \"%s\"? Say it, e.g. \"create a vendor bill from this PDF\".",
                attachment.name,
            ), 'is_error': True}
        company = self.env.company.name
        request = (
            f"{question}\n(The values are those of the document \"{attachment.name}\" below, sent by the user. The "
            "customer or vendor is the other party of the document, never the company of the user, that sends or "
            f"receives it: the user's company is \"{company}\", which is never that partner, even when the document "
            "names it as its customer. On a bill from a vendor, the vendor is the company that issued it, whose name "
            "usually heads the document; on a document sent to a customer, it is that customer.)\n"
            f"Document:\n{text}"
        )
        if candidate.get('path') and self._get_import_context(candidate):
            # the record is named after its menu: a Bill, a Credit Note, not a Journal Entry
            menu = candidate['path'].rpartition('/')[2]
            candidate = dict(candidate, label=menu[:-1] if menu.endswith('s') and not menu.endswith('ss') else menu)
        # the company of the user is never the partner of a record drafted from a document
        values = self.with_context(ai_chat_exclude_partner=self.env.company.partner_id.id)._draft_record(
            request, candidate, usage)
        if result := values.get('result'):
            result['document'] = {'name': attachment.name, 'id': attachment.id}
        if values.get('content'):
            values['content'] = self.env._("I read \"%(file)s\". %(answer)s", file=attachment.name,
                                           answer=values['content'])
        return values

    @api.model
    def _answer_about_document(self, question, attachment, usage):
        """ Answer a question on a document, from its text. """
        text = self._read_document(attachment, usage)
        answer = self._text_chat(
            "Answer the question of a user on the document they sent, using only its text below. Be concise: at most "
            "150 words, plain text. Say so when the document does not answer the question.\n"
            f"Question: {question}\nDocument \"{attachment.name}\":\n{text}", usage,
        )
        return {'content': answer.strip(), 'source': 'openrouter_olg' if usage['ai_called'] else 'olg'}


def _get_pdf_text(raw):
    """ The text of a PDF, empty when it holds none (a scan). """
    try:
        reader = PdfReader(io.BytesIO(raw), strict=False)
        return "\n".join((page.extract_text() or '') for page in reader.pages[:MAX_PDF_PAGES])
    except Exception as error:  # noqa: BLE001 - any error of the PDF reader: read as a scan
        _logger.info("AI Chat Pro: the text of a PDF could not be read: %s", error)
        return ''
