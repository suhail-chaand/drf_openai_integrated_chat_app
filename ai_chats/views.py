import os
import json
import openai
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (ListAPIView,
                                     CreateAPIView,
                                     GenericAPIView)

from .models import Conversation
from .serializers import (ChatSerializer,
                          ConversationSerializer,
                          ChatConversationSerializer)

openai.api_key = os.getenv('OPENAI_API_KEY')

fine_tunes = ("ada:ft-personal:superhero-describer-2023-04-19-07-36-42",
              "ada:ft-personal:davinci-superhero-describer-2023-04-20-06-27-54")
edit_models = ("code-davinci-edit-001", "text-davinci-edit-001")
chat_completion_models = ("gpt-3.5-turbo", "gpt-3.5-turbo-0301")
completion_models = ("text-ada-001", "text-babbage-001", "text-curie-001", "text-davinci-002", "text-davinci-003")


def get_model_response(model, conversations):
    if model in chat_completion_models:
        model_response = openai.ChatCompletion.create(
            model=model,
            messages=conversations,
            max_tokens=1024
        )["choices"][0]["message"]["content"]
    else:
        prompt = str()
        for conversation in conversations:
            prompt += f"-{conversation['role'][0:1]}> {conversation['content']}\n"
        prompt = prompt + '-a> '

        model_response = openai.Completion.create(
            model=model,
            prompt=prompt,
            max_tokens=1024
        )["choices"][0]["text"]

    return {"role": "assistant", "content": model_response}


class CreateChatSession(CreateAPIView):
    serializer_class = ChatSerializer

    def post(self, request, *args, **kwargs):
        try:
            if request.data["model"] in chat_completion_models + completion_models + fine_tunes:
                conversations = [
                    {"role": "system", "content": "You are a friendly chat-bot "
                                                  "who provides precise response to human queries."},
                    {"role": "user", "content": request.data["content"]}
                ]

                conversations.append(get_model_response(
                    model=request.data["model"], conversations=conversations))

                chat_serialized = self.get_serializer(data={})
                chat_serialized.is_valid(raise_exception=True)
                chat_instance = chat_serialized.save()

                for conversation in conversations:
                    conversation.update({"chat": chat_instance.id})

                conversations_serialized = ConversationSerializer(data=conversations, many=True)
                conversations_serialized.is_valid(raise_exception=True)
                conversations_serialized.save()

                return Response({"data": conversations_serialized.data}, status=status.HTTP_200_OK)

            else:
                return Response({"error": f"The model: `{request.data['model']}` does not exist"},
                                status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class GetChatConversations(ListAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(chat=self.kwargs["pk"]).order_by('id')

    def get(self, request, *args, **kwargs):
        return Response({"data": self.get_serializer(self.get_queryset(), many=True).data},
                        status=status.HTTP_200_OK)


class GetModelResponse(GenericAPIView):
    serializer_class = ChatConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(chat=self.kwargs["pk"]).order_by('id')

    def post(self, request, **kwargs):
        try:
            if request.data["model"] in chat_completion_models + completion_models + fine_tunes:
                chat_history = self.get_serializer(self.get_queryset(), many=True).data
                conversations = [{
                    "role": "user", "content": request.data["content"]
                }]

                conversations.append(get_model_response(
                    model=request.data["model"], conversations=chat_history + conversations))

                for conversation in conversations:
                    conversation.update({"chat": kwargs["pk"]})

                conversations_serialized = ConversationSerializer(data=conversations, many=True)
                conversations_serialized.is_valid(raise_exception=True)
                conversations_serialized.save()

                return Response({"data": conversations_serialized.data}, status=status.HTTP_200_OK)

            else:
                return Response({"error": f"The model: `{request.data['model']}` does not exist"},
                                status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            return Response({"error": str(exception)}, status=status.HTTP_400_BAD_REQUEST)


def stream_model_response(model, chat_id, chat_history, conversations):
    response = {
        "status_code": status.HTTP_200_OK,
        "data": None,
        "error": None,
        "message": "SUCCESS"
    }
    try:
        model_response = {"role": "assistant", "content": str()}
        if model in chat_completion_models:
            for chunk in openai.ChatCompletion.create(
                    model=model,
                    messages=chat_history + conversations,
                    max_tokens=1024,
                    stream=True
            ):
                model_response["content"] += chunk["choices"][0]["message"]["content"]
                response["data"] = chunk["choices"][0]["message"]["content"]
                yield json.dumps(response) + "\n"
        else:
            prompt = str()
            for conversation in chat_history + conversations:
                prompt += f"-{conversation['role'][0:1]}> {conversation['content']}\n"
            prompt = prompt + '-a> '

            for chunk in openai.Completion.create(
                    model=model,
                    prompt=prompt,
                    max_tokens=1024,
                    stream=True
            ):
                model_response["content"] += chunk["choices"][0]["text"]
                response["data"] = chunk["choices"][0]["text"]
                yield json.dumps(response) + "\n"

        conversations.append(model_response)

        for conversation in conversations:
            conversation.update({"chat": chat_id})

        conversations_serialized = ConversationSerializer(data=conversations, many=True)
        conversations_serialized.is_valid(raise_exception=True)
        conversations_serialized.save()

    except Exception as exception:
        response.update({
            "status_code": status.HTTP_400_BAD_REQUEST,
            "error": str(exception),
            "message": "FAILURE"
        })
        yield json.dumps(response) + "\n"


class StreamModelResponse(GenericAPIView):
    serializer_class = ChatConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(chat=self.kwargs["pk"]).order_by('id')

    def post(self, request, **kwargs):
        if request.data["model"] in chat_completion_models + completion_models + fine_tunes:
            chat_history = self.get_serializer(self.get_queryset(), many=True).data
            conversations = [{
                "role": "user", "content": request.data["content"]
            }]

            return StreamingHttpResponse(stream_model_response(model=request.data["model"],
                                                               chat_id=kwargs["pk"],
                                                               chat_history=chat_history,
                                                               conversations=conversations),
                                         content_type='text/event-stream')

        else:
            return Response({"error": f"The model: `{request.data['model']}` does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)
