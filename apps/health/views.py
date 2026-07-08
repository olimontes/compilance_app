from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework import decorators, permissions, response, status


@extend_schema(
    responses=inline_serializer(
        name="HealthcheckResponse",
        fields={
            "status": serializers.CharField(),
            "environment": serializers.CharField(),
            "debug": serializers.BooleanField(),
            "database": serializers.CharField(),
            "database_error": serializers.CharField(required=False),
        },
    )
)
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


@extend_schema(exclude=True)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAdminUser])
def error_probe(request):
    raise RuntimeError("Intentional production error probe.")
