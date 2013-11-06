Django Yet Another Class Based View
===================================

django-yacbv (YetAnotherClassBasedView) is replacement of django's CBV
(django.views.generic.View).

* Django's View can only dispatch corresponds to request.method.
  but in many cases, it should consider more things, such as request parameter.
* Django's ClassBasedGenericView is inflexible, hard to remember it's API
  and hard to understand succession inheritances.
* Django's View can't remove decorators, this is necessary for testing.
  it forces us to test views with decorators, always it obstructs to
  pure unit testing.

As these solution, django-yacbv is released.

YACBV is simple
===============

django-yacbv provide simple class based view, allowing user to create more flexible
dispatching, like this:

.. code-block:: python

    from yacbv import View, view_config


    class TopView(View):
        @view_config(method='get',
                     param='flip',
                     template_name='top2.html')
        def flipped(self, request):
            return {'word': request.GET['flip']}

        @view_config(method='get',
                     template_name='top.html')
        def get(self, request):
            return {'word': 'world'}

Notice about them:

* The `flip` method will be dispatched only case that Request object contains `flip` parameter.
* The template for each views can be specified as `template_name` argument of `view_config`.
* These returned dictionary will be used as context for Template.

Now, django-yacbv is just pre-alpha library, not for production.
If you like this package, check out it from `Github <https://github.com/hirokiky/django-yacbv/>`_!
