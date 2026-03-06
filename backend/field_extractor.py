def detect_field_type(field):

    field = field.lower()

    if "password" in field:
        return "password"

    if "email" in field or "mail" in field:
        return "email"

    if "phone" in field or "phone number" in field:
        return "tel"

    if "dob" in field or "date of birth" in field:
        return "date"

    if "age" in field or "income" in field or "salary" in field:
        return "number"

    if "address" in field:
        return "textarea"

    return "text"


def build_field_schema(fields):

    schema = {}

    for field in fields:

        field_type = detect_field_type(field)

        schema[field] = {
            "type": field_type
        }

    return schema