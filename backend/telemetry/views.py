from django.shortcuts import render
from django.http import httpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from telemetry.models import *
from telemetry.serializers import *


# Create your views here.
