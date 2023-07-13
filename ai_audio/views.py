import os
import openai
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

openai.api_key = os.getenv('OPENAI_API_KEY')

# Create your views here.


class Transcribe(GenericAPIView):
    def post(self, request):
        """
        Request open-ai audio processing endpoint to transcribe the
        input audio file and save the response in a .srt file.
        """
        audio_file_path = request.data['audio_file_path']
        if audio_file_path.endswith(('.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm')):
            response_file_path = audio_file_path.replace(audio_file_path.split('.')[-1], 'transcript.srt')
            response_file = open(response_file_path, 'w')
            response_file.write(openai.Audio.transcribe(
                model='whisper-1',
                file=open(audio_file_path, 'rb'),
                response_format='srt'
            ))
            response_file.close()

            return Response({'data': response_file_path},
                            status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unsupported file format!'},
                            status=status.HTTP_400_BAD_REQUEST)


class Translate(GenericAPIView):
    def post(self, request):
        """
        Request open-ai audio processing endpoint to translate the
        input audio file and save the response in a .srt file.
        """
        audio_file_path = request.data['audio_file_path']
        if audio_file_path.endswith(('.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm')):
            response_file_path = audio_file_path.replace(audio_file_path.split('.')[-1], 'translation.srt')
            response_file = open(response_file_path, 'w')
            response_file.write(openai.Audio.translate(
                model='whisper-1',
                file=open(audio_file_path, 'rb'),
                prompt='Return english translation',
                response_format='srt'
            ))
            response_file.close()

            return Response({'data': response_file_path},
                            status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unsupported file format!'},
                            status=status.HTTP_400_BAD_REQUEST)
