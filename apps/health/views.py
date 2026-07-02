from django.conf import settings
from django.db import connection
from rest_framework import decorators, permissions, response, status


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.AllowAny])
def healthcheck(request):
    database_ok = True
    database_error = ""

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        database_ok = False
        database_error = str(exc)

    payload = {
        "status": "ok" if database_ok else "degraded",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database": "ok" if database_ok else "error",
    }
    if database_error:
        payload["database_error"] = database_error

    return response.Response(
        payload,
        status=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAdminUser])
def error_probe(request):
    raise RuntimeError("Intentional production error probe.")
