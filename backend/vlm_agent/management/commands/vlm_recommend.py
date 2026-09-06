import json

from django.core.management.base import BaseCommand, CommandError

from telemetry.models import Farm, FarmDevice
from vlm_agent.services import NoDeviceError, generate_recommendation


class Command(BaseCommand):
    help = "Generate a quality-gated VLM recommendation for a farm."

    def add_arguments(self, parser):
        parser.add_argument("farm_id", type=int)
        parser.add_argument("--device-id", type=int)

    def handle(self, *args, **options):
        farm = Farm.objects.filter(id=options["farm_id"]).first()
        if farm is None:
            raise CommandError(f"Farm {options['farm_id']} not found.")

        device = None
        if options["device_id"] is not None:
            device = FarmDevice.objects.filter(id=options["device_id"], farm=farm).first()
            if device is None:
                raise CommandError(f"Device {options['device_id']} was not found on farm {farm.id}.")

        try:
            result = generate_recommendation(farm, device=device)
        except NoDeviceError as exc:
            raise CommandError(str(exc))
        self.stdout.write(json.dumps(result, indent=2))
