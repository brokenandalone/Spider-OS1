"""Read-only assignment overview; uncertain dates stay explicitly undated."""
from datetime import date


def overview(rows, today=None):
    today = today or date.today()
    result = {'open':0, 'complete':0, 'overdue':0, 'undated':0, 'upcoming':[]}
    for row in rows:
        if row['status'] == 'Complete':
            result['complete'] += 1
            continue
        result['open'] += 1
        try:
            due = date.fromisoformat(row['due'].strip())
        except (ValueError, AttributeError):
            result['undated'] += 1
            continue
        if due < today: result['overdue'] += 1
        result['upcoming'].append({**dict(row), 'due_date':due})
    result['upcoming'].sort(key=lambda row:(row['due_date'], row['title']))
    return result
