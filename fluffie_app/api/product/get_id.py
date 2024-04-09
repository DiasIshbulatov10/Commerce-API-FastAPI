from asyncio import gather
from bson import ObjectId

from .route import router
from ...core.exceptions import NotFoundItem
from ...models.single_product import ProductModel
from ...config.positivelabels import positivelabels

@router.get(
  '/get/{id}',
  response_model=dict,
  responses=dict(
    (NotFoundItem.openapi_schema,),
  ),
)
async def get_product_id(id: str):
  query = {
    'label': { '$in': positivelabels['positive'] }
  }

  future = ProductModel.get(id)

  result, result1 = await gather(
    future,
    ProductModel.aggregate([
      {
        '$match': { '_id': ObjectId(id) }
      },
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
        '$lookup': {
          'from': "product_label_summaries",
          'localField': "review_prod_id",
          'foreignField': "prod_id",
          'as': "pl_summary",
        },
      },
      # {
      #   '$project': {
      #     "reviews.labels": 1,
      #     'rating': {
      #       '$avg': "$reviews.rating"
      #     },
      #     'total_reviews': { '$size': "$reviews" },
      #   },
      # },
      {
        '$facet': {
          'labelsdata': [
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
                },
                'id': { '$first': "$_id" },
                'label_tag': { '$first': "$reviews.labels.label" },
                'total_reviews': { '$first': "$total_reviews" },
                'rating': { '$first': "$rating" },
                'reviews': {
                  '$sum': 1,
                },
              },
            },
            { '$sort': { 'reviews': -1 } },
            {
              '$group': {
                '_id': {
                  '_id': "$id",
                },
                'id': { '$first': "$_id" },
                'total_reviews': { '$first': "$total_reviews" },
                'rating': { '$first': "$rating" },
                'reviews_labels': {
                  '$push': {
                    'label': { '$convert': { 'input': '$label_tag', 'to': 'objectId', 'onError': '$label_tag', 'onNull': '' } },
                    'reviews': "$reviews"
                  },
                },
              },
            },
            {
              '$project': {
                'id': 1,
                'total_reviews': 1,
                'rating': 1,
                'filtered_labels': {
                  '$filter': {
                    'input': "$reviews_labels",
                    'as': "item",
                    'cond': {
                      '$ne': ["$$item.label", None]
                    }
                  },
                },
              },
            },
            { '$sort': { "filtered_labels.reviews": -1 } },
            { '$unset': "_id" },
            { '$unset': "id" },
            {
              '$lookup': {
                'from': "labels",
                'localField': "filtered_labels.label",
                'foreignField': "_id",
                'as': "labels",
              },
            },
          ],
          'labelsdata1': [
            {
              '$project': {
                'reviews': 1,
              },
            },
          ],
          'labelsdata2': [
            {
              '$project': {
                'pl_summary': {
                    '_id': 1,
                    'prod_id': 1,
                    'insights': 1,
                    },
              },
            },
          ]
        }
      }
    ], allowDiskUse = True ).to_list(),
    # LabelModel.aggregate([
    #   {
    #     '$match': query
    #   },
    #   {
    #     '$project': {
    #       "_id": 1
    #     }
    #   }],
    #   allowDiskUse=True
    # ).to_list(),
  )

  if result is None:
    raise NotFoundItem('Product does not exist')

  result3 = []
  labelsdata = None
  if len(result1) > 0 and result1[0].get('labelsdata')\
    and len(result1[0]['labelsdata']) > 0:
    labelsdata = result1[0]['labelsdata'][0]

    if labelsdata.get('filtered_labels'):
      filtered_labels: list[dict] = labelsdata['filtered_labels']
      _labels = labelsdata.get('labels', [])

      for filtered_label in filtered_labels:
        f_label = filtered_label.copy()

        for _label in _labels:
          if filtered_label.get('label') == _label.get('_id'):
            f_label.update(_label)
            break

        result3.append(f_label)
  # result3 = result1[0]?.labelsdata[0]?.filtered_labels?.map((filtered_label) => {
  #     result4 = result1[0]?.labelsdata[0]?.labels?.filter((label, index) => {
  #         return filtered_label.label == label._id.toString()
  #     })
  #     return { ...filtered_label, ...result4[0] }
  # })

  negativeReviews = [
    item
    for item in result3
    if any(lab for lab in positivelabels['negative'] if lab == item.get('label'))
  ]

  positiveReviews = [
    item
    for item in result3
    if any(lab for lab in positivelabels['positive'] if lab == item.get('label'))
  ]

  # Positive = result1[0]?.labelsdata1[0]?.reviews.filter((item, key) => {
  #     return item?.labels?.some((label) => {
  #         return positiveLabels.some(lab => lab._id == label?.label)
  #     })
  # })

  await result.fetch_all_links()
  await result.refined_category.fetch_all_links()
  
  returned_data = {
    **result.dict(by_alias=True),
    'filtered_labels': result3,
    'positive_labels': positiveReviews,
    'negative_labels': negativeReviews,
    'rating': labelsdata.get('rating') if labelsdata else None,
    'total_reviews': labelsdata.get('total_reviews') if labelsdata else None,
    'pl_summary': result1[0]['labelsdata2'] if result1[0]['labelsdata2'] else None,
  }

  return returned_data