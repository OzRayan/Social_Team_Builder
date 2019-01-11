from django.contrib import messages


class PageTitleMixin:
    """Page title mixin class
    - for class based views
    :argument: -page_title
    :methods: - get_page_title()
              - get_context_data()
    """
    page_title = ''

    def get_page_title(self):
        """:return: - page_title"""
        return self.page_title

    def get_context_data(self, **kwargs):
        """:return: - context data with page_title keyword"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context

