from fastapi import HTTPException


def handle_value_error(error: ValueError) -> HTTPException:
    message = str(error).lower()
    if "não encontrado" in message or "nao encontrado" in message:
        status_code = 404
    elif "permissão" in message or "permissao" in message or "negada" in message:
        status_code = 403
    else:
        status_code = 400
    return HTTPException(status_code=status_code, detail=str(error))


def run_use_case(callback):
    try:
        return callback()
    except ValueError as error:
        raise handle_value_error(error) from error
