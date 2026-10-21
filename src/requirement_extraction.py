"""Extract traceable requirement records locally, without sending PDF pages to a model."""
import re

VERSION = 1
HEADING = re.compile(r'^\s*((?:NFR|FR|REQ|BR|UR|SR)[- ]?\d{1,4})(?![-\w])\s*[:.\-–]?\s*(.*)$', re.I)
CRITERION = re.compile(r'^\s*((?:NFR|FR|REQ|BR|UR|SR)-\d+-AC\d+)\s*:\s*(.*)', re.I)
MODAL = re.compile(r'\b(?:shall|must|should|is required to)\b', re.I)


def extract_requirements(pages):
    candidates, current = [], None
    for page in pages:
        for raw in page['text'].splitlines():
            line = re.sub(r'\s+', ' ', raw).strip()
            if not line:
                continue
            match = HEADING.match(line)
            if match:
                if current:
                    candidates.append(current)
                identifier = re.sub(r'[- ]?', '', match[1].upper())
                identifier = re.sub(r'([A-Z]+)(\d+)', r'\1-\2', identifier)
                current = {'id': identifier, 'title': match[2], 'page': page['page'], 'lines': []}
            elif current:
                # Numbered section headings terminate a requirement's body.
                if re.match(r'^\d+\.\d+(?:\.\d+)*\s+[A-Z]', line):
                    candidates.append(current)
                    current = None
                else:
                    current['lines'].append(line)
    if current:
        candidates.append(current)
    records = {}
    for item in candidates:
        body = ' '.join(item['lines'])
        # Contents and traceability tables repeat IDs but contain no behaviour.
        if not MODAL.search(body) and not any(CRITERION.match(line) for line in item['lines']):
            continue
        criteria, description = [], []
        status = 'Source requirement'
        for line in item['lines']:
            if re.match(r'^(SD|PT)\s*[|｜]', line):
                status = 'Source-derived' if line.startswith('SD') else 'Proposed target'
                continue
            criterion = CRITERION.match(line)
            if criterion:
                criteria.append({'id': criterion[1].upper(), 'text': criterion[2]})
            elif criteria:
                if re.match(r'^(?:CL-\d+|\d+\s+[A-Z])', line):
                    break
                criteria[-1]['text'] += ' ' + line
            else:
                description.append(line)
        record = {key: item[key] for key in ('id', 'title', 'page')}
        record.update(text=' '.join(description), criteria=criteria, status=status)
        previous = records.get(item['id'])
        if previous is None or len(body) > len(previous['text']) + sum(len(c['text']) for c in previous['criteria']):
            records[item['id']] = record
    if records:
        return list(records.values())
    # Documents without IDs: retain the exact requirement sentence, with a local ID.
    seen = set()
    for page in pages:
        text = re.sub(r'\s+', ' ', page['text']).strip()
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            if MODAL.search(sentence) and sentence not in seen:
                seen.add(sentence)
                records[str(len(records))] = {
                    'id': f'REQ-{len(records) + 1:03}', 'title': 'Requirement statement',
                    'page': page['page'], 'text': sentence, 'criteria': [],
                    'status': 'Extracted statement — local ID',
                }
    return list(records.values())
