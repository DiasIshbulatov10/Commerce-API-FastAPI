
def convert_age_to_group(age):
    if isinstance(age, int):
        if age <= 17:
            return "17 or under"
        elif 18 <= age <= 24:
            return "18 to 24"
        elif 25 <= age <= 34:
            return "25 to 34"
        elif 35 <= age <= 44:
            return "35 to 44"
        elif 45 <= age <= 54:
            return "45 to 54"
        elif 55 <= age <= 64:
            return "55 to 64"
        else:
            return "65 or over"
    else:
        return None
