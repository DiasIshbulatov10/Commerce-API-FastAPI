from typing import Any, Optional, Union, Sequence, Type, Callable, get_origin, get_args
from enum import Enum
from functools import wraps, cache

from starlette.routing import BaseRoute
from starlette.responses import JSONResponse, Response
from fastapi import APIRouter
from fastapi.datastructures import Default
from fastapi import params
from fastapi.encoders import DictIntStrAny, SetIntStr
from fastapi.types import DecoratedCallable
from fastapi.routing import APIRoute
from fastapi.utils import (
    generate_unique_id,
)
from pydantic import BaseModel

@cache
def _build_return(M, origin):
    name = None

    if origin is list:
        name = f'List{get_args(M)[0].__name__}'
    else:
        name = M.__name__

    class ReturnModel(BaseModel):
        status: bool
        data: M

    ReturnModel.__name__ = f'Response{name}'

    return ReturnModel

@cache
def build_paging_return(M):
    class ReturnModel(PagingResponse):
        data: list[M]

    ReturnModel.__name__ = f'Paging{M.__name__}'

    return ReturnModel

class PagingResponse(BaseModel):
    status: bool = True
    data: Any
    count: Optional[int]
    page: Optional[int]
    limit: Optional[int]
    pages: Optional[int]
    query_id: Optional[str]


class MultipulResponse(BaseModel):
    status: bool = True
    data: Any


class CustomRoute(APIRouter):
    def api_route(
        self,
        path: str,
        *,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[list[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[dict[Union[int, str], dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[list[str]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Type[Response] = Default(JSONResponse),
        name: Optional[str] = None,
        callbacks: Optional[list[BaseRoute]] = None,
        openapi_extra: Optional[dict[str, Any]] = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            @wraps(func)
            async def _wrapper(*args, **kwargs):
                data = await func(*args, **kwargs)

                if isinstance(data, PagingResponse):
                    return data

                if isinstance(data, dict) or isinstance(data, list) or isinstance(data, BaseModel):
                    return {
                        'status': True,
                        'data': data
                    }

                return data

            _response_model = response_model

            if _response_model:
                origin = get_origin(response_model)

                if origin or not issubclass(_response_model, PagingResponse):
                    _response_model = _build_return(response_model, origin)

            self.add_api_route(
                path,
                _wrapper,
                response_model=_response_model,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                methods=methods,
                operation_id=operation_id,
                response_model_include=response_model_include,
                response_model_exclude=response_model_exclude,
                response_model_by_alias=response_model_by_alias,
                response_model_exclude_unset=response_model_exclude_unset,
                response_model_exclude_defaults=response_model_exclude_defaults,
                response_model_exclude_none=response_model_exclude_none,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func

        return decorator
