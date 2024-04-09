from fastapi import Body
from datetime import timedelta

from .route import router
from ...models.register import RegisterModel
from ...schema.register import RegisterSchema, UserInLogin
from ...core.hashing import Hasher
from ...core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from ...middleware.custom_response import JSONResponse
from .helper import helper_user_data



@router.post(
  '/login',
)
async def login_user(input: UserInLogin = Body(...)):
  
    exist = await RegisterModel.find_one({"phone_number": int(input.phone_number)})

    if exist is None:
        return JSONResponse({"success": False, "message": 'This User is not registered!'}, status_code=500)
    else:
        verify = Hasher.verify_password(input.password, exist.password)

        if verify:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = Hasher.create_access_token(
                data={"username": exist.phone_number}, expires_delta=access_token_expires
            )

            userData = helper_user_data(exist.dict())

            return JSONResponse({"success": True, "message": 'Login!', "user": userData, "token": token}, status_code=200)
        else:
            return JSONResponse({"success": False, "message": 'Password incorrect!'}, status_code=500)

    
