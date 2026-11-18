from fastapi import HTTPException


def fail(status, code, message):
    raise HTTPException(status_code=status, detail={'code': code, 'message': message})


def require(condition, status=409, code='invalid_transition', message='This action is not allowed in the current state.'):
    if not condition:
        fail(status, code, message)
