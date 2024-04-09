from asyncio import gather
from typing import Optional

from fastapi import Query
from bson import ObjectId

from .route import router
from ...models.review import ReviewModel
from ...models.single_product import ProductModel
from ...models.label import LabelModel
from ...config.positivelabels import positivelabels

@router.get('/{prod_id}')
async def get_review_product(
  prod_id: str,
  sentiment: Optional[str] = Query(None),
  age: Optional[str] = Query(None),
  # duration: Optional[str] = Query(None),
  skintype: Optional[str] = Query(None),
  product_aspect: Optional[str] = Query(None),
  label: Optional[str] = Query(None),
  location: Optional[list[str]] = Query(None),
):
  query = {
    'prod_id': prod_id,
  }

  if location is not None:
    query['country'] = { '$in': location }

  if age is not None:
    age_array = age.split("-")
    query['age'] = { '$gte': int(age_array[0]), '$lte': int(age_array[1]) }

  other_feature_labels = []
  other_feature_array = []
  skintype_labels = []
  skintype_label_filter = ''

  if product_aspect is not None:
    other_feature_labels = await LabelModel.aggregate(
      [
        {
          '$match': { 'label': { '$in': positivelabels[product_aspect.lower()] } }
        },
        {
          '$project': {
            "_id": 1
          }
        }
      ],
      allowDiskUse=True
    ).to_list()

    for _label in other_feature_labels:
      other_feature_array.append(str(_label['_id']))

  if skintype is not None:
    skintype_filter = ''
    sentiment1 = ' (negative)' if sentiment == 'negative' else ' (positive)'

    if (skintype.lower() == 'oily'):
      skintype_filter = 'oily skin'
    elif (skintype.lower() == 'dry'):
      skintype_filter = 'dry skin'
    elif (skintype.lower() == 'normal'):
      skintype_filter = 'normal skin'
    elif (skintype.lower() == 'combination'):
      skintype_filter = 'combination skin'
    elif (skintype.lower() == 'sensitive'):
      skintype_filter = 'sensitive skin'
    elif (skintype.lower() == 'acne prone'):
      skintype_filter = 'acne skin'

    skintype_filter = skintype_filter + sentiment1
    skintype_labels = await LabelModel.aggregate(
      [
        {
          '$match': { 'label': skintype_filter }
        },
        {
          '$project': {
            "_id": 1
          }
        }
      ],
      allowDiskUse=True,
    ).to_list()

    for _label in skintype_labels:
      skintype_label_filter = str(_label['_id'])

  result1, poslabels = await gather(
    ProductModel.aggregate([
      {
        '$match': { '_id': ObjectId(prod_id) }
      },
      {
        "$addFields": {
          "review_prod_id": { "$toString": "$_id" }
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
          "reviewsdata": "$reviews",
        },
      },
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
                'reviews_labels': {
                  #  $push: { label: { $toObjectId: "$label_tag" }, reviews: "$reviews" },
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
          ]
        }
      }
    ], allowDiskUse=True).to_list(),
    LabelModel.aggregate([
      {
        '$match': { 'label': { '$in': positivelabels['negative' if sentiment == 'negative' else 'positive'] } }
      },
      {
        '$project': {
          "_id": 1
        }
      }
    ], allowDiskUse=True,).to_list()
  )

  posarray = []
  for _label in poslabels:
    posarray.append(str(_label['_id']))

  if len(posarray) > 0:
    query['labels'] = { '$elemMatch': { 'label': { '$in': posarray } } }

  result = await ReviewModel.aggregate([
    {
      '$match': query,
    },
    {
      '$project': {
        "_id": "$_id",
        "review_id": "$review_id",
        #  "prod_id": "$prod_id",
        "name": "$name",
        "age": "$age",
        "title": "$title",
        "desc": "$desc",
        "rating": "$rating",
        "country": "$country",
        "sentiment": "$sentiment",
        "labels": "$labels",
        'total_labels': { '$size': "$labels" },
        "created_at": "$created_at",
        "updatedAt": "$updatedAt",
      },
    }
  ]).to_list()

  filtered_result: list = []
  if product_aspect is None:
    filtered_result = result
  else:
    for _review in result:
      if _review.get('labels')\
        and any(_item['label'] in other_feature_array for _item in _review['labels']):
        filtered_result.append(_review)
    # filtered_result = filtered_result.filter((review, key) => {
    #   return review.labels?.some((item, index) => {
    #     return other_feature_array.includes(item.label)
    #   })
    # })

  if skintype is not None:
    filtered_result = [
      _review
      for _review in filtered_result
      if _review.get('labels')\
        and any(_item['label'] == skintype_label_filter for _item in _review['labels'])
    ]
    # filtered_result = filtered_result.filter((review, key) => {
    #   return review.labels?.some((item, index) => {
    #     return skintype_label_filter == item.label
    #   })
    # })

  _label_review_count = {}
  for _review in filtered_result:
    for _label in _review.get('labels', []):
      _label_id = _label['label']

      if _label_review_count.get(_label_id) is None:
        _label_review_count[_label_id] = 1
      else:
        _label_review_count[_label_id] += 1
  # filtered_result.map((review, key) => {
  #   review.labels?.map((label, index) => {
  #     if (allLabels.some(item => label?.label == item.label)) {
  #       allLabels.map((item, i) => {
  #         if (label?.label == allLabels[i].label) {
  #           allLabels[i].reviews = allLabels[i].reviews + 1
  #         }
  #       })
  #     } else {
  #       allLabels.push({ label: label?.label, reviews: 1 })
  #     }
  #   })
  # })

  allLabels = [
    { 'label': l, 'reviews': r }
    for l, r in _label_review_count.items()
  ]
  allLabels.sort(key=lambda v: v['reviews'], reverse=True)

  result3 = []
  if len(result1) > 0 and len(result1[0]['labelsdata']) > 0:
    labelsdata = result1[0]['labelsdata'][0]

    if labelsdata.get('filtered_labels'):
      filtered_label_list: list[dict] = labelsdata['filtered_labels']

      for filtered_label in filtered_label_list:
        result4 = filtered_label.copy()
        if labelsdata.get('labels'):
          _labels: list[dict] = labelsdata['labels']

          for _l in _labels:
            if filtered_label.get('label') == _l['_id']:
              result4.update(_l)
              break

        result3.append(result4)

  # result3 = result1[0]?.labelsdata[0]?.filtered_labels?.map((filtered_label) => {
  #   result4 = result1[0]?.labelsdata[0]?.labels?.filter((label, index) => {
  #     return filtered_label.label == label._id.toString()
  #   })
  #   return { ...filtered_label, ...result4[0] }
  # })

  filtered_label = []
  labels_reviews = []
  if label:
    labels_reviews = [
      r
      for r in filtered_result
      if r.get('labels') and any(label == l.get('label') for l in r['labels'])
    ]
    # labels_reviews = filtered_result.filter((review, key) => {
    #   return review.labels?.some((item, index) => {
    #     return label == item.label
    #   })
    # })

    filtered_label = None

  else:
    if product_aspect:
      allLabels = [
        _l
        for _l in allLabels
        if any(_l['label'] == lab for lab in other_feature_array)
      ]
      # allLabels = allLabels?.filter(item => {
      #   return other_feature_array.some(lab => lab == item?.label)
      # })

    filtered_label = []
    for item in allLabels:
      for lab in result3:
        if lab.get('_id') and str(lab['_id']) == item['label']:
          filtered_label.append({
            **lab,
            'reviews': item['reviews'],
          })
          break
    # filtered_label = allLabels?.map(item => {
    #   labels = result3.filter(lab => lab._id == item?.label)
    #   return { ...labels[0], reviews: item.reviews }
    # })

  return {
    'reviews': labels_reviews if len(labels_reviews) > 0 else filtered_result,
    'filtered_label': filtered_label
  }

