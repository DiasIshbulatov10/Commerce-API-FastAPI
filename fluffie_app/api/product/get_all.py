from asyncio import gather
from math import ceil
from typing import Optional
import time

from fastapi import Query
from beanie.odm.enums import SortDirection
from bson import ObjectId

from .route import router
from ...models.single_product import ProductModel
from ...models.review import ReviewModel
from ...middleware.custom_response import PagingResponse

@router.get(
  '/',
  response_model=PagingResponse,
)
async def get_all_product(
  limit: Optional[int] = Query(10),
  page: Optional[int] = Query(1),
  title: Optional[str] = Query(None),
  category: Optional[list[str]] = Query(None),
  brand: Optional[str] = Query(None),
  refined_category: Optional[str] = Query(None),
  age_min: Optional[int] = Query(0),
  age_max: Optional[int] = Query(None),
  price_min: Optional[int] = Query(0),
  price_max: Optional[int] = Query(None),
):
  queryreview = {}
  if age_max:
    # agearray = age.split("-")
    queryreview['age'] = { '$gte': age_min, '$lte': age_max }

  query = {}
  if title:
      query['title'] = { '$regex': '.*' + title + '.*', '$options': 'i' }

  if price_min:
    query['price'] = { '$gte': price_min, '$lte': price_max }

  if brand:
    query['brand'] = brand

  if category:
    query['category'] = { '$in': category }

  if refined_category:
    query['refined_category'] = refined_category

  if page == 1:
    result, count = await gather(
      *[
        ProductModel.find(
          query,
          sort=[(ProductModel.created_at, SortDirection.DESCENDING)],
          skip=(page - 1) * limit,
          limit=limit, 
        ).to_list(),
        ProductModel.find(query).count()
      ]
    )


    await gather(*map(lambda v: v.fetch_link(ProductModel.brand), result))

    return PagingResponse(
      data=result,
      count=count,
      page=page,
      limit=limit,
      pages=ceil(count / limit)
    )
  else:
    count = await ProductModel.find(query).count()
    resultReview = []

    if age_max:
      resultReview = await ReviewModel.aggregate([
        {
          '$match': queryreview,
        },
        {
          '$group': {
            '_id': {
              '_id': "$_id",
              'prod_id': "$prod_id",
            },
            'id': { '$first': "$_id" },
            'prod': {
              '$sum': 1,
            },
          },
        },
        {
          '$project': {
            "_id": { "$toObjectId": "$_id._id" },
            "prod_id": "$_id.prod_id"
          },
        },
        { '$skip': limit * (page - 1) },
        { '$limit': limit }
      ], allowDiskUse=True).to_list()

      resultReview = [
        ObjectId(rev['prod_id'])
        for rev in resultReview
      ]

      if len(resultReview) != 0:
          query['_id'] = { '$in': resultReview }

    result = await ProductModel.aggregate([
        { '$match': query },
        {
          "$addFields": {
            "review_prod_id": { "$toString": "$_id" },
          },
        },
        {
          '$lookup': {
            'from': "reviews",
            'localField': "review_prod_id",
            'foreignField': "prod_id",
            'as': "reviews",
          },
        },
        {
          '$project': {
            "reviews.labels": 1,
            'rating': {
              '$avg': "$reviews.rating"
            },
            'total_reviews': { '$size': "$reviews" },
            "slug": "$slug",
            "title": "$title",
            "prod_link": "$prod_link",
            "price": "$price",
            "img": "$img",
            "brand": { '$toObjectId': "$brand" },
            "refined_category": "$refined_category",
          },
        },
        { '$unwind': { 'path': "$reviews", 'preserveNullAndEmptyArrays': True } },
        {
          '$unwind': {
            'path': "$reviews.labels",
            'preserveNullAndEmptyArrays': True,
          },
        },
        {
          '$group': {
            '_id': {
              '_id': "$_id",
              'label': "$reviews.labels.label",
              'rating': "$rating"
            },
            'id': { '$first': "$_id" },
            'title': { '$first': "$title" },
            # slug: { '$first': "$slug" },
            'brand': { '$first': "$brand" },
            'img': { '$first': "$img" },
            'price': { '$first': "$price" },
            # prod_link: { '$first': "$prod_link" },
            'refined_category': { '$first': "$refined_category" },
            'label_tag': { '$first': "$reviews.labels.label" },
            'total_reviews': { '$first': "$total_reviews" },
            'reviews': {
              '$sum': 1,
            },
          },
        },
        # { '$sort': { reviews: 1 } },
        {
          '$group': {
            '_id': {
                '_id': "$id",
                'rating': "$_id.rating",
            },
            'id': { '$first': "$id" },
            'title': { '$first': "$title" },
            # slug: { '$first': "$slug" },
            'brand': { '$first': "$brand" },
            'img': { '$first': "$img" },
            'price': { '$first': "$price" },
            # prod_link: { '$first': "$prod_link" },
            'refined_category': { '$first': "$refined_category" },
            'total_reviews': { '$first': "$total_reviews" },
            # rating: { '$first': "$rating" },
            'reviews_labels': {
              # '$push': { label: { '$toObjectId': "$label_tag" }, reviews: "$reviews" },
              '$push': {
                'label': {
                  '$convert': { 'input': '$label_tag', 'to': 'objectId', 'onError': '', 'onNull': '' }
                },
                'reviews': "$reviews"
              },
            },
          },
        },
        {
          '$project': {
            'id': 1,
            'total_reviews': 1,
            'rating': "$_id.rating",
            'slug': 1,
            'title': "$title",
            # prod_link: 1,
            'price': 1,
            'img': 1,
            'refined_category': "$refined_category",
            'brand': { '$toObjectId': "$brand" },
            'filtered_labels': {
              '$filter': {
                'input': "$reviews_labels",
                'as': "item",
                'cond': {
                  '$and': [
                    { '$ne': ["$$item.label", None] },
                    { '$ne': ["$$item.label", ''] }
                  ]
                }
              },
            },
          },
        },
        { '$unset': "_id" },
        { '$sort': { "filtered_labels.reviews": -1 } },
        {
          '$lookup': {
            'from': "brands",
            'localField': "brand",
            'foreignField': "_id",
            'as': "brand",
          },
        },
        # {
        #     '$addFields': {
        #         filtered_labels: { '$slice': ["$filtered_labels", 4] },
        #     },
        # },
        {
          '$lookup': {
            'from': "labels",
            'localField': "filtered_labels.label",
            'foreignField': "_id",
            'as': "labels",
          },
        },
        {
          '$addFields': {
            'refined_category_id': { '$convert': { 'input': '$refined_category', 'to': 'objectId', 'onError': '', 'onNull': '' } }
          },
        },
        {
          '$lookup': {
            'from': "refined_categories",
            'localField': "refined_category_id",
            'foreignField': "_id",
            'as': "refind_category",
          },
        },
        {
          '$set': {
            'refind_category': { '$arrayElemAt': ["$refind_category", 0] },
          }
        },
        {
          '$addFields': {
            'master_category_id': {
              '$convert': { 'input': '$refind_category.master_category_id', 'to': 'objectId', 'onError': '', 'onNull': '' }
            }
          },
        },
        {
          '$lookup': {
            'from': "master_categories",
            'localField': "master_category_id",
            'foreignField': "_id",
            'as': "master_category",
          },
        },
        {
          '$set': {
            'master_category': { '$arrayElemAt': ["$master_category", 0] },
          }
        },
        {
          '$set': {
            'brand': { '$arrayElemAt': ["$brand", 0] },
          }
        },
        { '$sort': { 'price': 1 } },
        { '$unset': "master_category_id" },
        { '$unset': "refined_category_id" },
        { '$unset': "refined_category" },
        { '$skip': limit * (page - 1) },
        { '$limit': limit }
    ], allowDiskUse=True).to_list()

    for _product in result:
      filtered_labels: list = _product['filtered_labels']
      filtered_labels.sort(key=lambda v: v['reviews'], reverse=True)

      _product['filtered_labels'] = filtered_labels[:4]

      labels = _product['labels']
      _product['labels'] = [
        l
        for l in labels
        if any(item for item in _product['filtered_labels'] if item['label'] == str(l['_id']))
      ]
    # result.map((product) => {
    #     product.filtered_labels = product.filtered_labels.sort(function (a, b) {
    #         return b.reviews - a.reviews
    #     }).slice(0, 4)
    #     product.labels = product.labels.filter(label => product.filtered_labels.some(item => item.label == label._id.toString()))
    # })

    return PagingResponse(
      data=result,
      count=count,
      page=page,
      limit=limit,
      pages=ceil(count / limit)
    )


