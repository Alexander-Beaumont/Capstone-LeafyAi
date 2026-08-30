from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from telemetry.models import (
    BatchPlacement,
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    PlantBatch,
)


def success_response(msg="", response_status=status.HTTP_200_OK):
    return Response(
        {
            "success": True,
            "succes": True,
            "msg": msg,
        },
        status=response_status,
    )


def error_response(msg, response_status=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "success": False,
            "succes": False,
            "msg": msg,
        },
        status=response_status,
    )


def date_to_datetime(value):
    if value is None:
        return None
    if hasattr(value, "hour"):
        return value
    return timezone.datetime.combine(
        value,
        timezone.datetime.min.time(),
        tzinfo=timezone.utc,
    )


def display_growth_stage(value):
    return {
        "seedling": "Seedling",
        "early_growth": "Vegetative",
        "mature": "Harvest",
    }.get(value, value)


def normalise_growth_stage(value):
    cleaned = (value or "seedling").strip().lower().replace("-", "_").replace(" ", "_")
    return {
        "seedling": "seedling",
        "vegetative": "early_growth",
        "early_growth": "early_growth",
        "mature": "mature",
        "harvest": "mature",
        "harvest_ready": "mature",
    }.get(cleaned, "seedling")


def display_status(value):
    return {
        "active": "Growing",
        "harvested": "Ready",
        "failed": "Terminated",
    }.get(value, value)


def normalise_status(value):
    cleaned = (value or "active").strip().lower().replace("-", "_").replace(" ", "_")
    return {
        "active": "active",
        "growing": "active",
        "in_progress": "active",
        "harvested": "harvested",
        "ready": "harvested",
        "completed": "harvested",
        "failed": "failed",
        "terminated": "failed",
    }.get(cleaned, "active")


def get_or_create_farm_level(level_number):
    farm, _ = Farm.objects.get_or_create(
        name="Default Farm",
        defaults={"location": ""},
    )
    device, _ = FarmDevice.objects.get_or_create(
        farm=farm,
        name="Default Device",
        defaults={"device_type": "farm"},
    )
    farm_level, _ = FarmLevel.objects.get_or_create(
        device=device,
        level_number=level_number,
    )
    return farm_level


def growing_area_response(area):
    placements = (
        BatchPlacement.objects.filter(growing_area=area)
        .select_related("plant_batch")
        .order_by("-start_date")
    )

    return {
        "growingAreaId": str(area.id),
        "growingAreaName": area.name,
        "slotCount": area.slot_count,
        "farmLevel": area.farm_level.level_number,
        "batches": [
            {
                "plantType": placement.plant_batch.plant_type,
                "batchPlantDate": date_to_datetime(placement.plant_batch.planting_date),
                "growthStage": display_growth_stage(placement.plant_batch.growth_stage),
                "status": display_status(placement.plant_batch.status),
                "batchId": str(placement.plant_batch.id),
                "GrowthAreaStartDate": placement.start_date,
                "GrowthAreaEndDate": placement.end_date,
            }
            for placement in placements
        ],
    }


def batch_response(batch):
    placements = (
        BatchPlacement.objects.filter(plant_batch=batch)
        .select_related("growing_area", "growing_area__farm_level")
        .order_by("-start_date")
    )

    return {
        "plantType": batch.plant_type,
        "batchPlantDate": date_to_datetime(batch.planting_date),
        "growthStage": display_growth_stage(batch.growth_stage),
        "status": display_status(batch.status),
        "batchId": str(batch.id),
        "growingAreas": [
            {
                "growingAreaId": str(placement.growing_area.id),
                "growingAreaName": placement.growing_area.name,
                "slotCount": placement.growing_area.slot_count,
                "farmLevel": placement.growing_area.farm_level.level_number,
                "startDate": placement.start_date,
                "endDate": placement.end_date,
            }
            for placement in placements
        ],
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def growing_areas(request):
    areas = GrowingArea.objects.select_related("farm_level").order_by("id")
    return Response([growing_area_response(area) for area in areas])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batches(request):
    plant_batches = PlantBatch.objects.order_by("-planting_date", "-id")
    return Response([batch_response(batch) for batch in plant_batches])


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def move_batch(request):
    batch = get_object_or_404(PlantBatch, id=request.data.get("batchID"))
    current_area = get_object_or_404(GrowingArea, id=request.data.get("currentGaID"))
    destination_area = get_object_or_404(GrowingArea, id=request.data.get("destinationGaID"))

    if current_area.id == destination_area.id:
        return error_response("Destination growing area must be different")

    current_placement = BatchPlacement.objects.filter(
        plant_batch=batch,
        growing_area=current_area,
        end_date__isnull=True,
    ).first()
    if current_placement is None:
        return error_response(
            "Batch is not currently in the provided growing area",
            status.HTTP_404_NOT_FOUND,
        )

    if BatchPlacement.objects.filter(growing_area=destination_area, end_date__isnull=True).exists():
        return error_response(
            "Destination growing area already has a batch move that batch first"
        )

    with transaction.atomic():
        now = timezone.now()
        current_placement.end_date = now
        current_placement.save(update_fields=["end_date"])
        BatchPlacement.objects.create(
            plant_batch=batch,
            growing_area=destination_area,
            start_date=now,
        )

    return success_response()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_growing_area(request):
    name = (request.data.get("name") or "").strip()
    if not name:
        return error_response("name is required")

    try:
        farm_level_number = int(request.data.get("farmLevel"))
    except (TypeError, ValueError):
        return error_response("farmLevel must be a number")

    if farm_level_number not in [1, 2]:
        return error_response("farmLevel must be 1 or 2")

    try:
        slot_count = int(request.data.get("slotCount"))
    except (TypeError, ValueError):
        return error_response("slotCount must be a number")

    if slot_count < 1:
        return error_response("slotCount must be at least 1")

    GrowingArea.objects.create(
        name=name,
        slot_count=slot_count,
        farm_level=get_or_create_farm_level(farm_level_number),
    )
    return success_response(response_status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_growing_area(request):
    growing_area = get_object_or_404(GrowingArea, id=request.data.get("growingAreaID"))

    name = request.data.get("name")
    if name is not None:
        cleaned_name = name.strip()
        if not cleaned_name:
            return error_response("name cannot be empty")
        growing_area.name = cleaned_name

    if "farmLevel" in request.data:
        try:
            farm_level_number = int(request.data.get("farmLevel"))
        except (TypeError, ValueError):
            return error_response("farmLevel must be a number")
        if farm_level_number not in [1, 2]:
            return error_response("farmLevel must be 1 or 2")
        growing_area.farm_level = get_or_create_farm_level(farm_level_number)

    if "slotCount" in request.data:
        try:
            slot_count = int(request.data.get("slotCount"))
        except (TypeError, ValueError):
            return error_response("slotCount must be a number")
        if slot_count < 1:
            return error_response("slotCount must be at least 1")
        growing_area.slot_count = slot_count

    growing_area.save()
    return success_response()


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_growing_area(request):
    growing_area = get_object_or_404(GrowingArea, id=request.data.get("growingAreaID"))

    with transaction.atomic():
        growing_area.delete()

    return success_response()


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_batch(request):
    batch = get_object_or_404(PlantBatch, id=request.data.get("batchID"))
    action = (request.data.get("action") or "").strip().lower()

    if action not in ["harvest", "terminate"]:
        return error_response('action must be either "harvest" or "terminate"')

    batch.status = "harvested" if action == "harvest" else "failed"
    if action == "harvest":
        batch.growth_stage = "mature"
    batch.save()

    BatchPlacement.objects.filter(plant_batch=batch, end_date__isnull=True).update(
        end_date=timezone.now()
    )
    return success_response()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_batch(request):
    growing_area = get_object_or_404(GrowingArea, id=request.data.get("growingAreaID"))

    if BatchPlacement.objects.filter(growing_area=growing_area, end_date__isnull=True).exists():
        return error_response(
            "Destination growing area already has a batch move that batch first"
        )

    plant_type = (request.data.get("plantType") or "").strip()
    if not plant_type:
        return error_response("plantType is required")

    batch = PlantBatch.objects.create(
        plant_type=plant_type,
        planting_date=timezone.localdate(),
        growth_stage=normalise_growth_stage(request.data.get("growthStage")),
        status=normalise_status(request.data.get("status")),
    )
    BatchPlacement.objects.create(
        plant_batch=batch,
        growing_area=growing_area,
        start_date=timezone.now(),
    )

    return success_response(response_status=status.HTTP_201_CREATED)
