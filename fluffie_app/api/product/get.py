from asyncio import gather
from bson import ObjectId

from .route import router
from ...core.exceptions import NotFoundItem
from ...models.single_product import ProductModel
from ...config.positivelabels import positivelabels
from ...middleware.custom_response import MultipulResponse

@router.get(
  '/get/multi/{ids}',
#   response_model=MultipulResponse,
)
async def get_multi_products(ids: str):
    result = ids.split(",")
    idList = []
    for id in result:
        idList.append(ObjectId(id))

    result = await ProductModel.aggregate([
        { '$match': {"_id": { "$in": idList }} },
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
        #         'filtered_labels': { '$slice': ["$filtered_labels", 4] },
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
        { '$unset': "master_category_id" },
        { '$unset': "refined_category_id" },
        { '$unset': "refined_category" },
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

    return result
