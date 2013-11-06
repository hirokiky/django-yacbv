import itertools
from functools import reduce

from django.http.response import Http404
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod


class ViewMetaClass(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(ViewMetaClass, cls).__new__
        new_class = super_new(cls, name, bases, attrs)

        new_class.views = [value for name, value in attrs.items()
                           if not name.startswith('_') and hasattr(value, '_wrapped')]
        new_class.views.sort(key=lambda x: x._order)
        return new_class


class View(metaclass=ViewMetaClass):
    """ Base View class.

    View class try to call methods wrapped by view_config:

    * Original View methods can be called without any decorators.
      This behavior is provided for ensuring depending-less tests.
    * When wrapped View raised ViewNotMatched, it will try next one.
    * All of views are not matched, it will return 404 response.

    You can inherit this class and register views methods.
    Then, decorate view methods with yacbv.view_config to apply
    configation to each view methods, such as witch views will
    be call or witch template to use.

    .. code-block:: python

       class DashboardView(View):
           @view_config(method='get')
           def get_view(self, request):
               return {'word', 'hello'}

           @view_config(method='post')
           def post_view(self, request):
               return {'word', 'posted'}

    Check the behavior of view_config for more detail.
    """
    views = []
    resource = (lambda s, x: x)

    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        def view(request, *args, **kwargs):
            self = cls(**initkwargs)

            for view in self.views:
                try:
                    return view._wrapped(self, request, *args, **kwargs)
                except ViewNotMatched:
                    continue
            else:
                raise Http404
        return view


class ViewNotMatched(Exception):
    """ Called view was not apposite.
    This exception is to notify Controllers that called view was not apposite
    to the applied rquest.
    """


def get_base_wrappers(method='get', template_name='', param='', predicates=()):
    """ basic View Wrappers used by view_config.
    """
    if param:
        predicates = (ParamPredicate(param),) + predicates

    wrappers = (preserve_view(MethodPredicate(method), *predicates),)

    if template_name:
        wrappers += (render_template(template_name),)

    return wrappers


_view_counter = itertools.count()


def view_config(
        method='get',
        template_name='',
        param='',
        predicates=(),
        base_wrappers_getter=get_base_wrappers,
):
    """ Creating View methods applied some configurations
    and store it to _wrapped attribute on each View methods.

    * _wrapped expects to be called by yacbv.View
      (subclasses of yacbv.View)
    * The original view will not be affected by this decorator.
    """
    wrappers = base_wrappers_getter(method, template_name, param, predicates)

    def wrapper(view_callable):
        def _wrapped(*args, **kwargs):
            return reduce(
                lambda a, b: b(a),
                reversed(wrappers + (view_callable,))
            )(*args, **kwargs)
        view_callable._wrapped = _wrapped
        view_callable._order = next(_view_counter)
        return view_callable
    return wrapper


def preserve_view(*predicates):
    """ Raising ViewNotMatched when applied request was not apposite.

    preserve_view calls all Predicates and when return values of them was
    all True it will call a wrapped view.
    It raises ViewNotMatched if this is not the case.

    Predicates:
    This decorator takes Predicates one or more, Predicate is callable
    to return True or False in response to inputted request.
    If the request was apposite it should return True.
    """
    def wrapper(view_callable):
        def _wrapped(self, request, *args, **kwargs):
            if all([predicate(request) for predicate in predicates]):
                return view_callable(self, request, *args, **kwargs)
            else:
                raise ViewNotMatched
        return _wrapped
    return wrapper


class MethodPredicate(object):
    """ Predicate class to checking Method of request object.

    MethodPredicate is preserve views when the request method was not same with
    applied in instantiate.
    """
    def __init__(self, method):
        self.method = method

    def __call__(self, request):
        return request.method.lower() == self.method.lower()


class ParamPredicate(object):
    """ Predicate class to checking request object has specified parameter.

    ParamPredicate is preserve views when the request method does not contained
    parameter specified when instantiated.
    """
    def __init__(self, param):
        self.param = param

    def __call__(self, request):
        return self.param in request.REQUEST


def render_template(template_name):
    """ Decorator to specify which template to use for Wrapped Views.

    It will return string rendered by specified template and
    returned dictionary from wrapped views as a context for template.
    The returned value was not dictionary, it does nothing,
    just returns the result.
    """
    def wrapper(func):
        def _wraped(self, request, *args, **kwargs):
            res = func(self, request, *args, **kwargs)
            if isinstance(res, dict):
                return TemplateResponse(request, template_name,
                                        context=res)
            else:
                return res
        return _wraped
    return wrapper
