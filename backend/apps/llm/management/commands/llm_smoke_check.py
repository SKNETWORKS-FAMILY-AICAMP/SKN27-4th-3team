from django.core.management.base import BaseCommand, CommandError

from backend.apps.llm import services as llm_services


class Command(BaseCommand):
    help = "Run the LLM provider smoke check for deployment verification."

    def handle(self, *args, **options):
        result = llm_services.run_required_provider_smoke_check()
        if result.ok:
            self.stdout.write(
                "llm smoke check ok "
                f"status={result.status} "
                f"required={str(result.required).lower()} "
                f"provider={result.provider} "
                f"model_id={result.model_id or ''}"
            )
            return

        raise CommandError(
            "llm smoke check failed "
            f"status={result.status} "
            f"reason={result.reason} "
            f"provider={result.provider} "
            f"model_id={result.model_id or ''}"
        )
