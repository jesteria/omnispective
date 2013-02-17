import json

from . import base, celery, settings


class OmnispectiveMiddleware(base.OmnispectiveClient):

    @staticmethod
    def enqueue_task(task_name, data):
        task = getattr(celery, task_name)
        task.delay(data)

    @staticmethod
    def parse_request(request):
        return json.dumps({
        })

    @staticmethod
    def parse_response(response):
        return json.dumps({
        })

    def process_response(self, request, response):
        request_data = self.parse_request(request)
        response_data = self.parse_response(response)
        if settings.USE_CELERY:
            self.enqueue_task('post_request', request_data)
            self.enqueue_task('post_response', response_data)
        else:
            self.post_request(request_data)
            self.post_response(response_data)
