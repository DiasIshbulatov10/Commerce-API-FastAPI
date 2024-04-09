import ujson
import asyncio


from datetime import datetime

from bson.objectid import ObjectId

from fluffie_app.db.redis import redis_async_conn

def serialize_data(obj): 
    if isinstance(obj, datetime): 
        return obj.isoformat() 
    if isinstance(obj, ObjectId): 
        return str(obj)
    raise TypeError("Type not serializable") 

_TTL = 3600

async def cache_get_label_master(query, type):
    if type == "all":
        if raw_data := await redis_async_conn.get(f'query_product_cache:positive_master_labels'):
            raw_data = ujson.loads(raw_data)
            return raw_data, [], query
    elif type == "by_label":
        labels_name = query["label"]["$in"]
        async with redis_async_conn.pipeline(transaction=True) as pipe:
            cached_labels, = await (pipe.mget(*[
                f"query_product_cache:positive_master_labels_{label}" for label in labels_name
                ]).execute())
        cached_labels = [ujson.loads(cached_label) for cached_label in cached_labels if cached_label is not None]
        cached_labels_name = [next(iter(cached_label)) for cached_label in cached_labels if cached_label is not None]
        non_cached = [label_name for label_name in labels_name if label_name not in cached_labels_name]
        query = {"label": {"$in": non_cached}}
        return cached_labels, non_cached, query
    return {}, [], query

def cache_set_label_master(data, type):
    if type == "all":
        asyncio.create_task(
            redis_async_conn.set(
                f'query_product_cache:positive_master_labels',
                ujson.dumps(data, default=serialize_data),
                ex=_TTL
            )
        )
    elif type == "by_label":
        for label in data:
            asyncio.create_task(
                redis_async_conn.set(
                    f'query_product_cache:positive_master_labels_{label}',
                    ujson.dumps({label: data[label]}, default=serialize_data),
                    ex=_TTL
                )
            )

async def cache_get_mutli_label_by_name(names):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_labels,  = await (pipe.mget(*[
            f"query_product_cache:positive_labels_{label}" for label in names
            ]).execute())
        cached_labels = [ujson.loads(cached_label) for cached_label in cached_labels if cached_label is not None]
        return cached_labels

def cache_set_label_by_name(name, data):
    asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:positive_labels_{name}',
            ujson.dumps({
                    "key": name,
                    "data": data
                },
                default=serialize_data
            ),
            ex=_TTL
        )
    )

async def cache_get_multi_brands_by_id(ids):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_brands,  = await (pipe.mget(*[
            f"query_product_cache:brand_{_id}" for _id in ids
            ]).execute())
        cached_brands = [ujson.loads(cached_brand) for cached_brand in cached_brands if cached_brand is not None]
        return cached_brands

def cache_set_brand_by_id(_id, data):
    asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:brand_{_id}',
            ujson.dumps(data, default=serialize_data),
            ex=_TTL
        )
    )

async def cache_get_multi_master_categories_by_id(ids):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_master_categories,  = await (pipe.mget(*[
            f"query_product_cache:master_category_{_id}" for _id in ids
            ]).execute())
        cached_master_categories = [ujson.loads(cached_master_category) for cached_master_category in cached_master_categories if cached_master_category is not None]
        return cached_master_categories

def cache_set_master_category_by_id(_id, data):
    asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:master_category_{_id}',
            ujson.dumps(data, default=serialize_data),
            ex=_TTL
        )
    )

async def cache_get_multi_refined_categories_by_id(ids):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_refined,  = await (pipe.mget(*[
            f"query_product_cache:refined_category_{_id}" for _id in ids
            ]).execute())
        cached_refined = [ujson.loads(cached_r) for cached_r in cached_refined if cached_r is not None]
        return cached_refined

def cache_set_refined_category_by_id(_id, data):
    asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:refined_category_{_id}',
            ujson.dumps(data, default=serialize_data),
            ex=_TTL
        )
    )

async def cache_get_multi_document_by_id(ids):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_documents,  = await (pipe.mget(*[
            f"query_product_cache:product_{_id}" for _id in ids
            ]).execute())
        cached_documents = [ujson.loads(cached_label) for cached_label in cached_documents if cached_label is not None]
        return cached_documents

def cache_set_document_by_id(_id, data):
    asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:product_{_id}',
            ujson.dumps(data, default=serialize_data),
            ex=_TTL
        )
    )

async def cache_get_multi_document_summary_by_id(ids):
    async with redis_async_conn.pipeline(transaction=True) as pipe:
        cached_documents,  = await (pipe.mget(*[
            f"query_product_cache:product_label_summaries_{_id}" for _id in ids
            ]).execute())
        cached_documents = [ujson.loads(cached_label) for cached_label in cached_documents if cached_label is not None]
        return cached_documents

async def cache_set_document_summary_by_id(_id, data):
    await asyncio.create_task(
        redis_async_conn.set(
            f'query_product_cache:product_label_summaries_{_id}',
            ujson.dumps(data, default=serialize_data),
            ex=_TTL
        )
    )

