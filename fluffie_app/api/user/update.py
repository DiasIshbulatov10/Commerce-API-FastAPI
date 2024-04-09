from .route import router
from ...models.register import RegisterModel
from ...middleware.custom_response import JSONResponse
from .helper import helper_user_data


@router.post(
  '/update',
)
async def update_user(data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return JSONResponse({"success": False, "message": 'No User Data Update!'}, status_code=400)
    user = await RegisterModel.find_one({"phone_number": int(data.get('phone_number'))})

    if user:
        # if data.get('phone_number'):
        #     user.phone_number = data.get('phone_number')
        if data.get('first_name'):
            user.first_name = data.get('first_name')
        if data.get('date_of_birth'):
            user.date_of_birth = data.get('date_of_birth')
        if data.get('gender'):
            user.gender = data.get('gender')


        updated_user = await user.save()

        response = helper_user_data(updated_user.dict())

        if updated_user:
            return JSONResponse({"success": True, "message": 'User Data Updated!!!', "user": response}, status_code=200)
        
        return JSONResponse({"success": False, "message": 'User Data Update Failed!'}, status_code=500)
    
    return JSONResponse({"success": False, "message": 'User Not Found!'}, status_code=500)
 

  