import json
import math
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qs

async def app(scope: dict, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
    assert scope['type'] == 'http'
    
    path = scope['path']
    method = scope['method']
    
    if method == 'GET':
        if path == '/factorial':
            await handle_factorial(scope, receive, send)
        elif path.startswith('/fibonacci/'):
            await handle_fibonacci(scope, receive, send)
        elif path == '/mean':
            await handle_mean(scope, receive, send)
        else:
            await send_error(send, 404, "Not Found")
    else:
        await send_error(send, 404, "Not Found")

async def handle_factorial(scope: dict, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
    query_string = scope['query_string'].decode()
    params = parse_qs(query_string)
    
    if 'n' not in params:
        await send_error(send, 422, "Missing 'n' parameter")
        return
    
    try:
        n = int(params['n'][0])
        if n < 0:
            await send_error(send, 400, "Factorial is undefined for negative integers")
            return
        result = math.factorial(n)
        await send_json(send, {"result": result})
    except ValueError:
        await send_error(send, 422, "Invalid 'n' parameter")

async def handle_fibonacci(scope: dict, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
    _, _, n_str = scope['path'].partition('/fibonacci/')
    
    try:
        n = int(n_str)
        if n < 0:
            await send_error(send, 400, "Fibonacci is undefined for negative integers")
            return
        result = fibonacci(n)
        await send_json(send, {"result": result})
    except ValueError:
        await send_error(send, 422, "Invalid 'n' parameter")

async def handle_mean(scope: dict, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
    body = await receive_body(receive)
    
    try:
        data = json.loads(body)
        if not isinstance(data, list):
            await send_error(send, 400, "Data must be an array")
            return
        if not data:
            await send_error(send, 400, "Array must not be empty")
            return
        if not all(isinstance(x, (int, float)) for x in data):
            await send_error(send, 422, "Array elements must be numbers")
            return
        result = sum(data) / len(data)
        await send_json(send, {"result": result})
    except json.JSONDecodeError:
        await send_error(send, 422, "Invalid JSON")

async def receive_body(receive: Callable[[], Awaitable[dict]]) -> str:
    body = b''
    more_body = True
    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)
    return body.decode()

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

async def send_json(send: Callable[[dict], Awaitable[None]], data: dict, status: int = 200) -> None:
    body = json.dumps(data).encode('utf-8')
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [
            (b'content-type', b'application/json'),
        ]
    })
    await send({
        'type': 'http.response.body',
        'body': body,
    })

async def send_error(send: Callable[[dict], Awaitable[None]], status: int, message: str) -> None:
    await send_json(send, {"error": message}, status)