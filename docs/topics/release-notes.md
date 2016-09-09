# Release Notes

## 2.0

* Upload and download support.
* Media type changes from `application/vnd.coreapi+json` to `application/coreapi+json`.
  For backwards compatibility, either are currently accepted.
* Codec methods `dump()`/`load()` become `encode()`/`decode()`. The old style
  methods currently continue to work for backward compatibility.
* The client instance validates that passed parameters match the available parameter names.
  Fails if unknown parameters are included, or required parameters are not included.
* `.action()` now accepts a `validate=False` argument, to turn off parameter validation.
* Parameter values are validated against the encoding used on the link to ensure
  that they can be represented in the request.
* `type` annotation added to `Field` instances.
* `multipart/form-data` is now consistently used on multipart links, even when
  no file arguments are passed.
* `action`, `encoding`, and `transform` parameters to `.action()` now replaced with a
  single `overrides` argument. The old style arguments currently continue to work for
  backward compatibility.
* The `supports` attribute is no longer used when defining codec classes. A
  `supports` property currently exists on the base class, to provide backwards
  compatibility for `coreapi-cli`.

The various backwards compatibility shims are planned to be removed in the 2.1 release.
