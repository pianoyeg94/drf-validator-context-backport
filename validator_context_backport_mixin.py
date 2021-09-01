import threading
import functools

from django.utils.functional import classproperty
from rest_framework.fields import Field


class ValidatorContextBackwardsCompatibilityMixin:
    """
    A mixin used to provide backward-compatibility between different
    version of DRF, in particular version 3.9 and 3.13.
    
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
    """
    _original_dunder_call = None
    _dunder_call_lock = None
    
    @classproperty
    def _dunder_call_modification_guard(cls) -> threading.Lock:
        # each inheritor class gets its own instance of `threading.Lock()`
        if not cls._dunder_call_lock:
            cls._dunder_call_lock = threading.Lock()
        return cls._dunder_call_lock
    
    @classmethod
    def _provide_context_to_dunder_call(cls, context: Field) -> None:
        # retrieve the original  `__call__`
        cls.__call__ = cls._original_dunder_call
        # get the name of the second param from  `__call__` (context)
        context_param_name = cls.__call__.__code__.co_varnames[2]
        # at runtime override the original `__call__` and pass it the required
        # context through the partialmethod
        cls.__call__ = functools.partialmethod(
            cls.__call__,
            **{context_param_name: context}
        )
    
    @classmethod
    def _save_original_dunder_call(cls) -> None:
        cls._original_dunder_call = cls.__call__
    
    @classmethod
    def _disable_requires_context_flag(cls) -> None:
        # ensure that no conflicts occur when DRF 3.11 - 3.12 is being used
        # because the deprecated `.set_context()` method still gets called
        cls.requires_context = False
    
    def set_context(self, context: Field) -> None:
        # prevent race conditions in the context of 2 or more request-response
        # cycles (usually different OS threads, depending on 
        # the wsgi server implementation)
        with self._dunder_call_modification_guard:
            if not self._original_dunder_call:
                self._save_original_dunder_call()
                self._disable_requires_context_flag()
            self._provide_context_to_dunder_call(context)
