from .route import router
from ...models.register import RegisterModel
from ...middleware.custom_response import JSONResponse
from ...core.hashing import Hasher
from .helper import helper_user_data


@router.post(
  '/changePassword',
)
async def change_password(data: dict):
    
    id = data.get('id')
    user = await RegisterModel.get(id)

    if user:
        passHash = Hasher.get_password_hash(data.get('password'))
        
        user.password = passHash
        updated_user = await user.save()

        # response = helper_user_data(updated_user.dict())

        if updated_user:
            return JSONResponse({"success": True, "message": 'Password Changed!!!'}, status_code=200)
        
        return JSONResponse({"success": False, "message": 'Password Change Failed!'}, status_code=500)
    
    return JSONResponse({"success": False, "message": 'User Not Found!'}, status_code=500)
 

  