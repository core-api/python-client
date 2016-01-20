from coreapi.compat import string_types
from coreapi.document import Document, Link
from coreapi.exceptions import NodeLookupError
import collections


Ancestor = collections.namedtuple('Ancestor', ['document', 'keys'])


def validate_is_primative(value):
    """
    When calling a link, parameter values must be primatives.
    """
    if isinstance(value, dict):
        if any([not isinstance(key, string_types) for key in value.keys()]):
            raise TypeError("Invalid parameter. Dictionary keys must be strings.")
        for item in value.values():
            validate_is_primative(item)
        return
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_is_primative(item)
        return
    elif (
        value is None or
        isinstance(value, string_types) or
        isinstance(value, (int, float, bool))
    ):
        return

    raise TypeError("Invalid parameter type. Got '%s'." % type(value))


def validate_parameters(link, parameters):
    """
    Ensure that parameters passed to the link are correct.

    Raises a `ValueError` if any parameters do not validate.
    """
    # Ensure all parameter values are valid types.
    for value in parameters.values():
        validate_is_primative(value)


def validate_keys_to_link(document, keys):
    """
    Validates that keys looking up a link are correct.

    Returns a two-tuple of (link, link_ancestors).
    """
    if not isinstance(keys, (list, tuple)):
        msg = "'keys' must be a list of strings or intes."
        raise TypeError(msg)
    if any([
        not isinstance(key, string_types) and not isinstance(key, int)
        for key in keys
    ]):
        raise TypeError("'keys' must be a list of strings or ints.")

    # Determine the link node being acted on, and its parent document.
    # 'node' is the link we're calling the action for.
    # 'document_keys' is the list of keys to the link's parent document.
    node = document
    link_ancestors = [Ancestor(document=document, keys=[])]
    for idx, key in enumerate(keys, start=1):
        try:
            node = node[key]
        except (KeyError, IndexError):
            index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
            msg = 'Index %s did not reference a link. Key %s was not found.'
            raise NodeLookupError(msg % (index_string, repr(key).strip('u')))
        if isinstance(node, Document):
            ancestor = Ancestor(document=node, keys=keys[:idx])
            link_ancestors.append(ancestor)

    # Ensure that we've correctly indexed into a link.
    if not isinstance(node, Link):
        index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
        msg = "Can only call 'action' on a Link. Index %s returned type '%s'."
        raise NodeLookupError(
            msg % (index_string, type(node).__name__)
        )

    return (node, link_ancestors)
