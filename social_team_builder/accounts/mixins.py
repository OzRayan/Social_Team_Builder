from django.contrib import messages


class PageTitleMixin:
    page_title = ''

    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        return context


class InfoMixin:
    info_message = ''

    def get_info_message(self):
        return '{}'.format(self.info_message)

    def form_valid(self, form):
        info_message = self.get_info_message()
        if info_message:
            messages.info(self.request, info_message)
        return super(InfoMixin, self).form_valid(form)


class SuccessMixin:
    success_message = ''

    def get_success_message(self):
        return '{}'.format(self.success_message)

    def form_valid(self, form):
        success_message = self.get_success_message()
        if success_message:
            messages.success(self.request, success_message)
        return super(SuccessMixin, self).form_valid(form)


class ErrorMixin:
    error_message = ''

    def get_error_message(self):
        return '{}'.format(self.error_message)

    def form_invalid(self, form):
        error_message = self.get_error_message()
        if error_message:
            messages.error(self.request, error_message)
        return super(ErrorMixin, self).form_invalid(form)



