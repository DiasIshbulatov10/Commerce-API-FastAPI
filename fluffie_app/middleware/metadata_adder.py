from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.datastructures import MutableHeaders

class MetaDataAdderMiddleware:
    application_generic_urls = ['/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc']

    def __init__(
            self,
            app: ASGIApp
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not any(scope["path"].startswith(endpoint) for endpoint in MetaDataAdderMiddleware.application_generic_urls):
            responder = MetaDataAdderMiddlewareResponder(self.app)
            await responder(scope, receive, send)
            return
        await self.app(scope, receive, send)


class MetaDataAdderMiddlewareResponder:

    def __init__(
            self,
            app: ASGIApp,
    ) -> None:
        """
        """
        self.app = app
        self.initial_message: Message = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.send = send
        await self.app(scope, receive, self.send_with_meta_response)

    async def send_with_meta_response(self, message: Message):
        message_type = message["type"]

        if message_type == "http.response.start":
            # Don't send the initial message until we've determined how to
            # modify the outgoing headers correctly.
            self.initial_message = message

        elif message_type == "http.response.body":
            response_body: bytes = message["body"]

            if self.initial_message['status'] < 300:
                data_to_be_sent_to_user = b'{"status":true,"data":' + response_body + b'}'
            else:
                data_to_be_sent_to_user = b'{"status":false,' + response_body[1:]

            headers = MutableHeaders(raw=self.initial_message["headers"])
            headers["Content-Length"] = str(len(data_to_be_sent_to_user))
            message["body"] = data_to_be_sent_to_user

            await self.send(self.initial_message)
            await self.send(message)
