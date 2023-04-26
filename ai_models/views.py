import os
import openai
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class ModelsList(ListAPIView):
    def get(self, request, *args, **kwargs):
        try:
            return Response({"data": openai.Model.list()}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class FineTunesList(ListAPIView):
    def get(self, request, *args, **kwargs):
        try:
            return Response({"data": openai.FineTune.list()}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)
