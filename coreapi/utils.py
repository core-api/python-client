from coreapi.document import Array


def dotted_path_to_list(doc, path):
    """
    Given a document and a string dotted notation like 'rows.123.edit",
    return a list of keys,such as ['rows', 123, 'edit'].
    """
    keys = path.split('.')
    active = doc
    for idx, key in enumerate(keys):
        # Coerce array lookups to integers.
        if isinstance(active, Array):
            try:
                key = int(key)
                keys[idx] = key
            except:
                pass

        # Descend through the document, so we can correctly identify
        # any nested array lookups.
        try:
            active = active[key]
        except (KeyError, IndexError, ValueError, TypeError):
            break
    return keys
