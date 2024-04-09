from .route import router
from ...models.register import RegisterModel
from ...middleware.custom_response import JSONResponse
from .helper import helper_user_data


@router.post(
  '/get/{id}',
)
async def get_user(id: str):
    user = await RegisterModel.get(id)

    if user:
        response = helper_user_data(user.dict())
        return JSONResponse({"success": True, "message": 'User Data Load Successful!!!', "user": response}, status_code=200)
    
    return JSONResponse({"success": False, "message": 'User Not Found!'}, status_code=500)
 

  