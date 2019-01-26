# NOTE: # noinspection - prefixed comments are for pycharm editor only
# for ignoring PEP 8 style highlights


class PageTitleMixin:
    """Page title mixin class
    - for class based views
    :argument: -page_title
    :methods: - get_page_title()
              - get_context_data()
    """
    page_title = ''

    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        # noinspection PyUnresolvedReferences
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context
