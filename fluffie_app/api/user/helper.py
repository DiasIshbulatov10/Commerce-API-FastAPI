def helper_user_data(data) -> dict:
  return {
    "id": str(data["id"]),
    "phone_number": data["phone_number"],
    "first_name": data["first_name"],
    "date_of_birth": data["date_of_birth"],
    "gender": data["gender"],
}


def helper_user_preferance(data) -> dict:
  return {
    "id": str(data["id"]),
    "phone_number": data["phone_number"],
    "skin_type": data["skin_type"],
    "skin_concerns": data["skin_concerns"],
    "skincare_price_range_preference": data["skincare_price_range_preference"],
    "skin_tone": data["skin_tone"],
    "skincare_product_preferences": data["skincare_product_preferences"],
    "sensitive_skin": data["sensitive_skin"],
    "skincare_insights": data["skincare_insights"],
  }