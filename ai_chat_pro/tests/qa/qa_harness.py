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

"""Run the QA cases against a database, with the live AI services, everything rolled back.

Usage (from the Odoo root):
    QA_ONLY=c12,c13 QA_GROUP=create .venv/bin/python odoo-bin shell -c odoo.conf -d <db> --no-http < qa_harness.py
"""
import base64
import importlib.util
import json
import os
import sys
import time
import traceback

QA_DIR = os.environ.get('QA_DIR') or os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.environ['QA_DIR']
spec = importlib.util.spec_from_file_location('qa_cases', os.path.join(QA_DIR, 'qa_cases.py'))
qa_cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa_cases)

only = {name for name in (os.environ.get('QA_ONLY') or '').split(',') if name}
group = os.environ.get('QA_GROUP') or ''
cases = [case for case in qa_cases.CASES if (not only or case['id'] in only) and (not group or case['group'] == group)]

from unittest.mock import patch
from odoo.addons.ai_chat_pro.models.ai_chat_agent import AiChatAssistant as Agent
LAST_INTENTS = {}
_orig_understand = Agent._understand
def _spy_understand(self_, question, usage, previous_plan=None, attachments=None):
    intent = _orig_understand(self_, question, usage, previous_plan, attachments)
    LAST_INTENTS[question] = {k: intent.get(k) for k in ('intent', 'target', 'parts', 'names', 'terms', 'question', 'multi_step', 'reference')}
    return intent
patch.object(Agent, '_understand', _spy_understand).start()
admin = env.ref('base.user_admin')
env = env(user=admin)
env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.allow_create', True)
env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.deep_analysis', True)
env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.use_olg', True)
Conversation = env['ai.chat.conversation']


def mention_of(spec):
    """ {model, name} -> mention dict, by exact name search. """
    Model = env[spec['model']]
    found = Model.name_search(spec['name'], limit=5)
    exact = [rid for rid, name in found if name.strip().lower() == spec['name'].lower()] or [rid for rid, _n in found]
    if not exact:
        raise ValueError(f"no {spec['model']} named {spec['name']!r}")
    return {'model': spec['model'], 'id': exact[0]}


def describe_answer(answer):
    res = answer.get('result') or {}
    steps = res.get('steps') or ([res] if res.get('type') == 'draft' else [])
    out = {
        'content': answer.get('content'), 'is_error': answer.get('is_error'), 'type': res.get('type'),
        'model': res.get('row_model') or res.get('model'), 'rows': len(res.get('rows') or []),
        'suggestions': answer.get('suggestions'), 'thoughts': answer.get('thoughts'),
        'intents': dict(LAST_INTENTS),
        'steps': [{'model': s.get('model'), 'title': s.get('title'), 'values': s.get('values'),
                   'warnings': s.get('warnings'), 'missing': s.get('missing'), 'choices': s.get('choices')} for s in steps],
        'copy_of': res.get('copy_of'), 'chart': res.get('chart'), 'columns': [c.get('label') if isinstance(c, dict) else c for c in res.get('columns') or []],
        'first_cells': [r.get('cells') if isinstance(r, dict) else r for r in (res.get('rows') or [])[:3]],
        'contexts': [s.get('context') for s in steps],
        'tokens': answer.get('tokens'), 'cost': answer.get('cost'), 'source': answer.get('source'),
    }
    return out


def run_case(case):
    problems = []
    created = []
    LAST_INTENTS.clear()
    conv_id = False
    answers = []
    if case.get('setup'):
        case['setup'](env)
    questions = case.get('steps') or [case['question']]
    for index, question in enumerate(questions):
        if question.startswith('$suggestion:'):
            # the user clicks a suggestion of the previous answer
            suggestions = answers[-1].get('suggestions') or []
            number = int(question.split(':')[1])
            if number >= len(suggestions):
                problems.append(f"no suggestion {number} to click: {suggestions}")
                break
            question = suggestions[number]
        mentions = [mention_of(spec) for spec in case.get('mentions', [])] if index == len(questions) - 1 else None
        deep = bool(case.get('deep')) and index == len(questions) - 1
        attachment_ids = None
        if case.get('attachment') and index == len(questions) - 1:
            name, content = case['attachment']
            uploaded = Conversation.upload_chat_attachment(name, base64.b64encode(content.encode()).decode())
            attachment_ids = [uploaded['id']]
        out = Conversation.ask_question(conv_id, question, deep, attachment_ids, mentions)
        conv_id = out['conversation']['id']
        answers.append(out['messages'][1])
        if case.get('create_each') and index < len(questions) - 1 and (out['messages'][1].get('result') or {}).get('type') in ('draft', 'plan'):
            # the records drafted by the earlier turns are created, as a user would
            for _ in (out['messages'][1]['result'].get('steps') or [None]):
                Conversation.create_draft_record(out['messages'][1]['id'])
    answer = answers[-1]
    desc = describe_answer(answer)
    exp = case.get('expect') or {}
    res = answer.get('result') or {}
    if 'error' in exp and bool(answer.get('is_error')) != exp['error']:
        problems.append(f"is_error={answer.get('is_error')} expected {exp['error']}")
    if 'something went wrong' in (answer.get('content') or '').lower():
        problems.append("crash: " + answer['content'])
    if 'type' in exp and res.get('type') != exp['type']:
        problems.append(f"type={res.get('type')} expected {exp['type']}")
    if 'model' in exp and desc['model'] != exp['model']:
        problems.append(f"model={desc['model']} expected {exp['model']}")
    if 'steps' in exp and [s['model'] for s in desc['steps']] != exp['steps']:
        problems.append(f"steps={[s['model'] for s in desc['steps']]} expected {exp['steps']}")
    for text in exp.get('content', []) if isinstance(exp.get('content'), list) else ([exp['content']] if exp.get('content') else []):
        if text.lower() not in (answer.get('content') or '').lower():
            problems.append(f"content lacks {text!r}: {answer.get('content')!r}")
    for text in exp.get('not_content', []):
        if text.lower() in (answer.get('content') or '').lower():
            problems.append(f"content has {text!r}")
    if 'rows_min' in exp and desc['rows'] < exp['rows_min']:
        problems.append(f"rows={desc['rows']} < {exp['rows_min']}")
    if 'rows_max' in exp and desc['rows'] > exp['rows_max']:
        problems.append(f"rows={desc['rows']} > {exp['rows_max']}")
    if 'suggestions_min' in exp and len(answer.get('suggestions') or []) < exp['suggestions_min']:
        problems.append(f"suggestions={answer.get('suggestions')}")
    if exp.get('values'):
        last = desc['steps'][-1]['values'] if desc['steps'] else {}
        for key, value in exp['values'].items():
            if value is None:
                if key not in last:
                    problems.append(f"values lack {key}: {last}")
            elif last.get(key) != value:
                problems.append(f"values[{key}]={last.get(key)!r} expected {value!r}")
    if exp.get('no_warnings') and any(s.get('warnings') for s in desc['steps']):
        problems.append(f"warnings: {[s.get('warnings') for s in desc['steps']]}")
    if exp.get('create') and res.get('type') in ('draft', 'plan', 'import') and not problems:
        steps = res.get('steps') or [res]
        for _ in steps:
            try:
                out = Conversation.create_draft_record(answer['id'])
            except Exception as error:
                problems.append(f"create failed: {error!r}")
                break
        final = env['ai.chat.message'].browse(answer['id']).result
        for step in (final.get('steps') or [final]):
            if step.get('res_id'):
                created.append(env[step['model']].browse(step['res_id']))
        desc['created'] = [(r._name, r.display_name) for r in created]
    if exp.get('verify') and not problems:
        try:
            verdict = exp['verify'](env, answer, created)
            if verdict:
                problems.append(f"verify: {verdict}")
        except Exception as error:
            problems.append(f"verify crashed: {error!r}\n{traceback.format_exc()[-800:]}")
    return problems, desc, answers


results = []
started = time.time()
for case in cases:
    env.cr.execute("SAVEPOINT qa_case")
    try:
        problems, desc, answers = run_case(case)
    except Exception as error:
        problems, desc = [f"exception: {error!r}\n{traceback.format_exc()[-1500:]}"], {}
    env.cr.execute("ROLLBACK TO SAVEPOINT qa_case")
    status = 'PASS' if not problems else 'FAIL'
    results.append({'id': case['id'], 'group': case['group'], 'question': case.get('question') or case.get('steps'),
                    'status': status, 'problems': problems, 'answer': desc})
    for problem in problems:
        print("   -", problem.replace("\n", "\n     ")[:1500])
    sys.stdout.flush()

env.cr.rollback()
passed = sum(1 for r in results if r['status'] == 'PASS')
with open(os.path.join(QA_DIR, os.environ.get('QA_OUT') or 'qa_results.json'), 'w') as handle:
    json.dump(results, handle, indent=1, default=str)
