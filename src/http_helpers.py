from flask import jsonify, request

from .errors import ApplicationError
from .validation import invalid


def body():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ApplicationError("The JSON body must be an object.")
    return data


def query_parameters(allowed):
    unknown = set(request.args) - set(allowed)
    if unknown:
        invalid(sorted(unknown)[0], "Unknown query parameter.")
    for field in request.args:
        if len(request.args.getlist(field)) != 1:
            invalid(field, "Query parameters must not be repeated.")
    return request.args.to_dict()


def pagination(parameters):
    result = []
    for field, default, maximum in (("page", 1, 1_000_000), ("page_size", 20, 100)):
        value = parameters.pop(field, str(default))
        if not value.isascii() or not value.isdecimal():
            invalid(field, "Must be a positive integer.")
        try:
            number = int(value)
        except ValueError:
            invalid(field, "Integer is too large.")
        if not 1 <= number <= maximum:
            invalid(field, f"Must be between 1 and {maximum}.")
        result.append(number)
    return tuple(result)


def collection(items, total, page, page_size):
    return jsonify({
        "items": items,
        "pagination": {
            "page": page, "page_size": page_size, "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
    })


def created(item, location):
    response = jsonify(item)
    response.status_code = 201
    response.headers["Location"] = location
    return response
