from fastapi import Body

from .route import router
from ...models.preferance import PreferanceModel
from ...schema.preferance import PreferanceSchema

from ...middleware.custom_response import JSONResponse
from .helper import helper_user_preferance


@router.post(
  '/preferance/save',
)
async def create_preferance(input: PreferanceSchema = Body(...)):
  
  exist = await PreferanceModel.find_one({"phone_number": input.phone_number})

  if exist is None:
    preferance = PreferanceModel(
      **input.dict()
    )

    created_preferance = await preferance.save()

    response = helper_user_preferance(created_preferance.dict())

    return JSONResponse({"success": True, "message": "New User's Preferance Created!!!", "preferance": response}, status_code=200)
  else:
    return JSONResponse({"success": False, "message": "This User's preferance already exists"}, status_code=500)


  