# drf-validator-context-backport

A mixin used to provide backward-compatibility between different
versions of DRF, in particular version 3.9 and 3.13.

When using version 3.9 the serializer context gets passed into the
validator by calling its `.set_context()` method.

Starting with version 3.11 to get the serializer context a class-based
validator has the ability to set its `.requires_context` class attribute
to True, resulting in the context being passed right into the validator's
`__call__` method as the 2nd parameter. In that case, the `.set_context()`
method isn't called at all.

When using this mixin with the old 3.9 version of DRF you can leverage
the new `.requires_context` class attribute as if you're already using
at least version 3.11.

When DRF version 3.13 gets released the `.set_context()` methdod will
not be called anymore and without this mixin all legacy code still
using the `.set_context()` method will just break.
