from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from telemetry.models import (
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    PlantBatch,
    BatchPlacement,
    Camera,
    CameraImage,
    Sensor,
    SensorReading,
    NutrientTank,
    Doser,
    SafeRange,
)

class FarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = Farm

        fields = [
            "id",
            "name",
            "location",
        ]


class FarmDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = FarmDevice

        fields = [
            "id",
            "farm",
            "name",
            "device_type",
        ]


class FarmLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = FarmLevel

        fields = [
            "id",
            "device",
            "level_number",
        ]


class GrowingAreaSerializer(serializers.ModelSerializer):

    class Meta:
        model = GrowingArea

        fields = [
            "id",
            "farm_level",
            "name",
        ]

class PlantBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlantBatch

        fields = [
            "id",
            "plant_type",
            "planting_date",
            "growth_stage",
            "status",
        ]


class BatchPlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = BatchPlacement

        fields = [
            "id",
            "plant_batch",
            "growing_area",
            "start_date",
            "end_date",
        ]


# ============================================================
# CAMERA
# ============================================================

class CameraSerializer(serializers.ModelSerializer):

    # Final API contract uses "farm_level_id"
    # rather than exposing the FK as "farm_level".
    farm_level_id = serializers.PrimaryKeyRelatedField(
        source="farm_level",
        queryset=FarmLevel.objects.all()
    )

    class Meta:
        model = Camera

        fields = [
            "id",
            "farm_level_id",
            "name",
            "position",

            "source_type",

            "ip_address",
            "rtsp_port",
            "rtsp_path",

            "webcam_index",

            "enabled",
            "cv_enabled",

            "capture_interval_minutes",

            "active_start_time",
            "active_end_time",

            "roi_points",

            "growth_baseline_reset_at",
        ]

        read_only_fields = [
            "id",
        ]

    # ========================================================
    # CAMERA VALIDATION
    # ========================================================

    def validate(self, attrs):
        """
        Validate final Camera contract.

        Supports both:
        - POST/create
        - PATCH/partial update

        When PATCH only supplies some fields, values already
        stored on the Camera are taken into account.
        """

        def get_value(field_name):
            """
            Return the value supplied in this request.

            If it was not supplied during PATCH, return the
            current value from the existing Camera.
            """

            if field_name in attrs:
                return attrs[field_name]

            if self.instance is not None:
                return getattr(
                    self.instance,
                    field_name,
                    None
                )

            return None

        # ----------------------------------------------------
        # SOURCE TYPE VALIDATION
        # ----------------------------------------------------

        source_type = get_value(
            "source_type"
        )

        ip_address = get_value(
            "ip_address"
        )

        rtsp_port = get_value(
            "rtsp_port"
        )

        rtsp_path = get_value(
            "rtsp_path"
        )

        webcam_index = get_value(
            "webcam_index"
        )

        source_errors = {}

        # ----------------------------------------------------
        # RTSP CAMERA
        # ----------------------------------------------------

        if source_type == "RTSP":

            if not ip_address:
                source_errors["ip_address"] = (
                    "ip_address is required for RTSP cameras."
                )

            if rtsp_port is None:
                source_errors["rtsp_port"] = (
                    "rtsp_port is required for RTSP cameras."
                )

            if not rtsp_path:
                source_errors["rtsp_path"] = (
                    "rtsp_path is required for RTSP cameras."
                )

            # WEBCAM-specific configuration should not remain
            # active on an RTSP Camera.
            attrs["webcam_index"] = None

        # ----------------------------------------------------
        # WEBCAM
        # ----------------------------------------------------

        elif source_type == "WEBCAM":

            if webcam_index is None:
                source_errors["webcam_index"] = (
                    "webcam_index is required for WEBCAM cameras."
                )

            # RTSP connection details are irrelevant to a
            # webcam and are normalised to NULL.
            attrs["ip_address"] = None
            attrs["rtsp_port"] = None
            attrs["rtsp_path"] = None

        if source_errors:
            raise serializers.ValidationError(
                source_errors
            )

        # ----------------------------------------------------
        # CAPTURE INTERVAL
        # ----------------------------------------------------

        capture_interval = get_value(
            "capture_interval_minutes"
        )

        if (
            capture_interval is not None
            and capture_interval < 1
        ):
            raise serializers.ValidationError(
                {
                    "capture_interval_minutes":
                        "capture_interval_minutes must be at least 1."
                }
            )

        # ----------------------------------------------------
        # ACTIVE CAPTURE WINDOW
        # ----------------------------------------------------

        active_start = get_value(
            "active_start_time"
        )

        active_end = get_value(
            "active_end_time"
        )

        # Either both times must exist or neither.
        if (
            (active_start is None)
            !=
            (active_end is None)
        ):
            raise serializers.ValidationError(
                {
                    "active_start_time":
                        "active_start_time and active_end_time "
                        "must both be set or both be null.",

                    "active_end_time":
                        "active_start_time and active_end_time "
                        "must both be set or both be null."
                }
            )

        # Equal times are specifically invalid.
        #
        # start < end:
        #     normal same-day window
        #
        # start > end:
        #     valid overnight window
        if (
            active_start is not None
            and active_end is not None
            and active_start == active_end
        ):
            raise serializers.ValidationError(
                {
                    "active_start_time":
                        "active_start_time and active_end_time "
                        "cannot be equal."
                }
            )

        # ----------------------------------------------------
        # ROI VALIDATION
        # ----------------------------------------------------

        roi = get_value(
            "roi_points"
        )

        if roi is not None:

            if not isinstance(roi, dict):
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI must be an object containing "
                            "x, y, width and height."
                    }
                )

            required_keys = {
                "x",
                "y",
                "width",
                "height",
            }

            if set(roi.keys()) != required_keys:
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI must contain exactly: "
                            "x, y, width and height."
                    }
                )

            try:
                x = Decimal(
                    str(roi["x"])
                )

                y = Decimal(
                    str(roi["y"])
                )

                width = Decimal(
                    str(roi["width"])
                )

                height = Decimal(
                    str(roi["height"])
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI x, y, width and height "
                            "must be numeric."
                    }
                )

            zero = Decimal("0")
            one = Decimal("1")

            # x and y are normalized coordinates.
            if (
                x < zero
                or x > one
                or y < zero
                or y > one
            ):
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI x and y must be between 0 and 1."
                    }
                )

            # Width/height must be positive and normalized.
            if (
                width <= zero
                or width > one
                or height <= zero
                or height > one
            ):
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI width and height must be greater "
                            "than 0 and no greater than 1."
                    }
                )

            # Rectangle cannot extend outside image.
            if x + width > one:
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI x + width cannot exceed 1."
                    }
                )

            if y + height > one:
                raise serializers.ValidationError(
                    {
                        "roi_points":
                            "ROI y + height cannot exceed 1."
                    }
                )

        return attrs



# ============================================================
# CAMERA IMAGE
# ============================================================

class CameraImageSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CameraImage

        fields = [
            "id",
            "camera",
            "captured_at",
            "image_url",
        ]

        read_only_fields = [
            "id",
            "image_url",
        ]

    def get_image_url(
        self,
        obj
    ):
        """
        Return the URL for the ImageField rather than exposing
        the internal filesystem location.
        """

        if not obj.path:
            return None

        try:
            return obj.path.url
        except ValueError:
            return None


# ============================================================
# SENSOR
# ============================================================

class SensorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor

        fields = [
            "id",
            "device",
            "sensor_type",
            "unit",
        ]


class SensorReadingSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = SensorReading

        fields = [
            "id",
            "sensor",
            "timestamp",
            "value",
        ]

        read_only_fields = [
            "timestamp",
        ]


# ============================================================
# HARDWARE
# ============================================================

class NutrientTankSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = NutrientTank

        fields = [
            "id",
            "device",
            "capacity_l",
            "current_level_l",
            "last_refill_date",
            "updated_at",
        ]

        read_only_fields = [
            "updated_at",
        ]


class DoserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doser

        fields = [
            "id",
            "device",
            "chemical_type",
            "concentration",
            "flow_rate_ml_per_min",
            "updated_at",
        ]

        read_only_fields = [
            "updated_at",
        ]


class SafeRangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SafeRange

        fields = [
            "id",
            "sensor_type",
            "min_value",
            "max_value",
            "severity",
        ]