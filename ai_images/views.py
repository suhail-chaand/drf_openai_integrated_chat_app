import os
import openai
import base64
from io import BytesIO
from PIL import (Image,
                 ImageDraw)
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

image_dimensions = ("256x256", "512x512", "1024x1024")


def _extract_file_name(file_path):
    return "".join(file_path.split("/")[-1].split(".")[0:-1])


def _get_resized_rgba_converted_image(image_file_path):
    image_buffer = BytesIO()
    Image.open(image_file_path).convert("RGBA").resize((256, 256)).save(image_buffer, 'png')
    return image_buffer.getvalue()


def _get_transparent_mask_image(edit_area_coordinates):
    mask = Image.new('RGBA', size=(256, 256), color=(0, 0, 0, 255))
    edit_area = ImageDraw.Draw(mask)
    for coordinates in edit_area_coordinates:
        edit_area.ellipse(coordinates, fill=0)

    image_buffer = BytesIO()
    mask.save(image_buffer, 'png')

    return image_buffer.getvalue()


def _write_b64_image_data_into_png_files(request_type, model_response, input_file_name=None):
    image_files = list()
    for image in model_response["data"]:
        image_files.append(
            f'ai_images/image_responses/{request_type}s/{request_type[0]}{model_response["created"]}'
            f'-{model_response["data"].index(image)}{f"_{input_file_name}" if input_file_name else ""}.png')

        with open(image_files[-1], "wb") as image_file:
            image_file.write(base64.b64decode(image["b64_json"]))

    return [f'{os.getenv("PROJECT_FOLDER_PATH")}{file_path}' for file_path in image_files]


class CreateImage(GenericAPIView):
    def post(self, request):
        try:
            if request.data["image_size"] in image_dimensions:
                return Response(
                    {"data": _write_b64_image_data_into_png_files(
                        request_type="creation",
                        model_response=openai.Image.create(
                            prompt=request.data["prompt"],
                            size=request.data["image_size"],
                            n=int(request.data["response_count"]),
                            response_format="b64_json"
                        )
                    )},
                    status=status.HTTP_200_OK
                )

            else:
                return Response({"error": "Invalid image size"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class CreateImageEdit(GenericAPIView):
    def post(self, request):
        try:
            if request.data["image_size"] in image_dimensions:
                input_file_name = _extract_file_name(request.data["file_path"])

                return Response(
                    {"data": _write_b64_image_data_into_png_files(
                        request_type="edit",
                        model_response=openai.Image.create_edit(
                            image=_get_resized_rgba_converted_image(
                                image_file_path=request.data["file_path"]),
                            mask=_get_transparent_mask_image(
                                edit_area_coordinates=request.data["edit_area_coordinates"]),
                            prompt=request.data["prompt"],
                            size=request.data["image_size"],
                            n=int(request.data["response_count"]),
                            response_format="b64_json"
                        ),
                        input_file_name=input_file_name
                    )},
                    status=status.HTTP_200_OK
                )

            else:
                return Response({"error": "Invalid image size"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class CreateImageVariation(GenericAPIView):
    def post(self, request):
        try:
            if request.data["image_size"] in image_dimensions:
                input_file_name = _extract_file_name(request.data["file_path"])

                return Response(
                    {"data": _write_b64_image_data_into_png_files(
                        request_type="variation",
                        model_response=openai.Image.create_variation(
                            image=_get_resized_rgba_converted_image(
                                image_file_path=request.data["file_path"]),
                            size=request.data["image_size"],
                            n=int(request.data["response_count"]),
                            response_format="b64_json"
                        ),
                        input_file_name=input_file_name
                    )},
                    status=status.HTTP_200_OK
                )

            else:
                return Response({"error": "Invalid image size"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)
