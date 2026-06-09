from django.conf import settings


def get_client_ip(request) -> str:
    remote_addr = request.META.get("REMOTE_ADDR") or "0.0.0.0"
    trusted_proxy_ips = set(getattr(settings, "DJANGO_TRUSTED_PROXY_IPS", ()))
    if remote_addr not in trusted_proxy_ips:
        return remote_addr

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    first_forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    return first_forwarded_ip or remote_addr


class TrustedProxyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        remote_addr = request.META.get("REMOTE_ADDR") or ""
        trusted_proxy_ips = set(getattr(settings, "DJANGO_TRUSTED_PROXY_IPS", ()))
        if remote_addr in trusted_proxy_ips:
            forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
            first_forwarded_proto = forwarded_proto.split(",", 1)[0].strip()
            if first_forwarded_proto == "https":
                request.META["HTTPS"] = "on"
                request.META["wsgi.url_scheme"] = "https"

        return self.get_response(request)
