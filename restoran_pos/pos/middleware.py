from django.db import OperationalError, ProgrammingError

from .models import SavedReceipt


class SavedReceiptCleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            SavedReceipt.delete_expired()
        except (OperationalError, ProgrammingError):
            pass

        return self.get_response(request)
