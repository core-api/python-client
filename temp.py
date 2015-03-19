from coreapi import Document, Link


def delete_note(note):
    return None

def edit_note(note, **kwargs):
    data = dict(note)
    data.update(**kwargs)
    return Document(data)

def create_note(root, **kwargs):
    note = Document({
      'meta': {'url': '/123', 'title': 'Note'},
      'description': kwargs.get('description', ''),
      'complete': False,
      'delete': Link('/123', action=delete_note),
      'edit': Link('/123', fields=[{'name': 'description', 'required': False}, {'name': 'complete', 'required': False}], action=edit_note)
    })
    data = dict(root)
    data['notes'] = list(data['notes'])
    data['notes'].insert(0, note)
    return Document(data)


doc = Document({
  'meta': {'url': '/', 'title': 'Notes'},
  'notes': [],
  'add_note': Link(url='/', fields=[{'name': 'description'}], action=create_note)
})

doc = doc.action(['add_note'], description='test')
doc = doc.action(['notes', 0, 'edit'], complete=True)
doc = doc.action(['add_note'], description='new')
doc = doc.action(['add_note'], description='new')
doc = doc.action(['notes', 0, 'edit'], description='very new')
doc = doc.action(['notes', 1, 'delete'])
print doc
