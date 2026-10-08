"""One-form paper builder with optional supplied text and reference entries."""
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit


class PaperDialog(QDialog):
    def __init__(self, parent=None, course=''):
        super().__init__(parent)
        self.setWindowTitle('APA student paper'); self.resize(620, 660)
        layout=QFormLayout(self); self.fields={}
        for key,label,default in [('title','Paper title',''), ('author','Your name',''),
                ('institution','Institution','Southern New Hampshire University'),
                ('course','Course',course), ('instructor','Instructor',''), ('due','Due date','')]:
            field=QLineEdit(default);self.fields[key]=field;layout.addRow(label,field)
        self.body=QTextEdit();self.body.setAcceptRichText(False)
        self.body.setPlaceholderText('Optional paper text. Separate paragraphs with a blank line.')
        layout.addRow('Paper text',self.body)
        self.references=QTextEdit();self.references.setAcceptRichText(False)
        self.references.setPlaceholderText('Optional reference entries. Separate entries with a blank line.')
        layout.addRow('References',self.references)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addRow(buttons)

    def values(self):
        values={key:field.text().strip() for key,field in self.fields.items()}
        values['paragraphs']=[x.strip() for x in self.body.toPlainText().split('\n\n') if x.strip()]
        values['references']=[x.strip() for x in self.references.toPlainText().split('\n\n') if x.strip()]
        return values
