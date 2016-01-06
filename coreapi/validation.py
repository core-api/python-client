from coreapi.compat import string_types


def validate_is_primative(value):
    """
    When calling a link, parameter values must be primatives.
    """
    if isinstance(value, dict):
        if any([not isinstance(key, string_types) for key in value.keys()]):
            raise TypeError("Invalid parameter. Dictionary keys must be strings.")
        for item in value.values():
            validate_is_primative(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_is_primative(item)
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
    provided = set(parameters.keys())
    required = set([
        field.name for field in link.fields if field.required
    ])
    optional = set([
        field.name for field in link.fields if not field.required
    ])

    # Determine any parameter names supplied that are not valid.
    unexpected = provided - (optional | required)
    unexpected = ['"' + item + '"' for item in sorted(unexpected)]
    if unexpected:
        fmt = 'Unknown parameter{plural}: {listing}'
        plural = 's' if len(unexpected) > 1 else ''
        listing = ', '.join(unexpected)
        raise ValueError(fmt.format(
            plural=plural,
            listing=listing
        ))

    # Determine if any required field names not supplied.
    missing = required - provided
    missing = ['"' + item + '"' for item in sorted(missing)]
    if missing:
        fmt = 'Missing required parameter{plural}: {listing}'
        plural = 's' if len(missing) > 1 else ''
        listing = ', '.join(missing)
        raise ValueError(fmt.format(
            plural=plural,
            listing=listing
        ))

    # Ensure all parameter values are valid types.
    for value in parameters.values():
            validate_is_primative(value)
