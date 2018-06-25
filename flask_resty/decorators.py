import functools

from . import context
from .utils import UNDEFINED

# -----------------------------------------------------------------------------


def get_item_or_404(func=None, **decorator_kwargs):
    # Allow using this as either a decorator or a decorator factory.
    if func is None:
        return functools.partial(get_item_or_404, **decorator_kwargs)

    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        id = self.get_data_id(kwargs)
        item = self.get_item_or_404(id, **decorator_kwargs)

        # No longer need these; just the item is enough.
        for id_field in self.id_fields:
            del kwargs[id_field]

        return func(self, item, *args, **kwargs)

    return wrapped


# -----------------------------------------------------------------------------


def request_cached_property(func):
    """Make the given method a per-request cached property.

    This caches the value on the request context rather than on the object
    itself, preventing problems if the object gets reused across multiple
    requests.
    """
    @property
    @functools.wraps(func)
    def wrapped(self):
        cached_value = context.get_for_view(self, func.__name__, UNDEFINED)
        if cached_value is not UNDEFINED:
            return cached_value

        value = func(self)
        context.set_for_view(self, func.__name__, value)

        return value

    return wrapped
