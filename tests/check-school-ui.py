"""Exercise School against a private temporary profile, including paper export."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication, QDialog
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'study'))
import store
import study
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    profile=Path(folder)
    with patch.object(store,'DATA_DIR',profile/'data'), \
         patch.object(store,'DB_PATH',profile/'data/study.db'), \
         patch.object(store,'DOCUMENTS_ROOT',profile/'Study'):
        panel=study.StudyWindow()
        assert panel.windowTitle()=='School | Spider OS'
        course=panel.current_course_id
        panel.store.add_assignment(course,'Essay','2026-10-09')
        panel.load_assignments()
        assert '1 open' in panel.dashboard.text()
        panel.notes.setPlainText('Saved course notes')
        values=dict(title='Test Paper',author='Student',institution='University',course='Course',instructor='Instructor',due='October 9, 2026',paragraphs=['Supplied text'],references=[])
        target=profile/'paper.docx'
        with patch.object(study.PaperDialog,'exec_',return_value=QDialog.Accepted), \
             patch.object(study.PaperDialog,'values',return_value=values), \
             patch.object(study.QFileDialog,'getSaveFileName',return_value=(str(target),'')):
            panel.create_apa_paper()
        assert target.is_file()
        with patch.object(panel,'launch') as launch:
            panel.open_snhu();assert launch.call_args.args[0]==['xdg-open','https://my.snhu.edu/']
        panel.close();app.processEvents()
        reopened=study.StudyWindow()
        assert reopened.notes.toPlainText()=='Saved course notes'
        assert '1 open' in reopened.dashboard.text()
        reopened.close()
print('School dashboard, APA export and existing-profile smoke checks passed.')
