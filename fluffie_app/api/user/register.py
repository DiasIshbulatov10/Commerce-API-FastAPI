from fastapi import Body

from .route import router
from ...models.register import RegisterModel
from ...schema.register import RegisterSchema
from ...core.hashing import Hasher

from ...middleware.custom_response import JSONResponse
from .helper import helper_user_data



@router.post(
  '/signup',
)
async def create_user(input: RegisterSchema = Body(...)):
  
  exist = await RegisterModel.find_one({"phone_number": int(input.phone_number)})

  if exist is None:
    passHash = Hasher.get_password_hash(input.password)

    input.password = passHash

    user = RegisterModel(
      **input.dict()
    )

    created_user = await user.save()

    response = helper_user_data(created_user.dict())

    return JSONResponse({"success": True, "message": 'New User Created!!!', "user": response}, status_code=200)
  else:
    return JSONResponse({"success": False, "message": 'Phone number already exists'}, status_code=500)


# Test API
@router.get(
  '/all',
)
async def get_all_user():
  all_users = await RegisterModel.all().to_list()

  return all_users
  