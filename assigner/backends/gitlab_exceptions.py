from requests.exceptions import HTTPError

from assigner.backends.exceptions import (
    UserInAssignerGroup,
    UserNotAssigned,
)

def raiseUserInAssignerGroup(err: HTTPError):
    """
    Request urls:
        PUT  /api/v4/projects/{}/members/{}
        POST /api/v4/projects/{}/members

    Expected response: HTTP 400 with json
    {'message': {'access_level': ['should be higher than Maintainer inherited membership from group assigner-testing']}}
    """
    if err.response.status_code != 400:
        return

    json = err.response.json()

    try:
        access_level_message = json["message"]["access_level"][0]
    except (KeyError, IndexError):
        return

    if "inherited membership from group" not in access_level_message:
        return

    raise UserInAssignerGroup(err)

def raiseUserNotAssigned(err: HTTPError):
    """
    Request url:
        PUT /api/v4/projects/{}/members/{}

    Expected response: HTTP 404
    """
    if err.response.status_code != 404:
        return

    raise UserNotAssigned(err)
