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


import tiktoken

AI_CHAT_SYSTEM_INSTRUCTION = "You are a friendly chat-bot who provides precise response to human queries."


def get_formatted_prompt(model_id, query, chat_history):
    """
    Function to format prompt based on model's API compatibility.
    :param model_id: Open-AI model ID
    :param query: Current user query
    :param chat_history: Chat history to maintain context
    :return: Formatted prompt
    """

    # Tokenization algorithm as per the model ID
    encoding = tiktoken.encoding_for_model(model_id)

    if model_id in completion_models:
        prompt = [f'-s> {AI_CHAT_SYSTEM_INSTRUCTION} ',
                  f'-u> {query["content"]} -a> ']
    else:
        prompt = [{'role': 'system', 'content': AI_CHAT_SYSTEM_INSTRUCTION},
                  {'role': 'user', 'content': query['content']}]

    # Get token count of the query
    tokens_count = len(encoding.encode(AI_CHAT_SYSTEM_INSTRUCTION)) + len(encoding.encode(query['content']))

    # Include chat history
    for conversation in chat_history:
        if conversation['role'] == 'assistant':
            query = chat_history[chat_history.index(conversation) - 1]['content']
            response = conversation['content']
            conversation_tokens_count = len(encoding.encode(query)) + len(encoding.encode(response))

            # Ensuring that the prompt does not consume the model's token limit of 4096
            if (tokens_count + conversation_tokens_count) <= (4096 - 1000):
                tokens_count += conversation_tokens_count
                if model_id in completion_models:
                    prompt.insert(1, f'-u> {query} ')
                    prompt.insert(2, f'-a> {response} ')
                else:
                    prompt.insert(1, {'role': 'user', 'content': query})
                    prompt.insert(2, {'role': 'assistant', 'content': response})
            else:
                break
    print(prompt)
    return prompt


def stream_model_response(model_id, chat_id, current_conversation, chat_history):
    streaming_response = str()
    model_response = {"role": "assistant", "content": str()}
    if model_id in completion_models:
        for chunk in openai.Completion.create(
                stream=True,
                model=model_id,
                prompt=get_formatted_prompt(model_id=model_id,
                                            query=current_conversation[0],
                                            chat_history=chat_history)
        ):
            model_response["content"] += chunk["choices"][0]["text"]
            streaming_response = chunk["choices"][0]["text"]
            yield json.dumps(streaming_response) + "\n"

    else:
        for chunk in openai.ChatCompletion.create(
                stream=True,
                model=model_id,
                messages=get_formatted_prompt(model_id=model_id,
                                              query=current_conversation[0],
                                              chat_history=chat_history)
        ):
            model_response["content"] += chunk["choices"][0]["message"]["content"]
            streaming_response = chunk["choices"][0]["message"]["content"]
            yield json.dumps(streaming_response) + "\n"

    current_conversation.append(model_response)

    for instance in current_conversation:
        instance.update({"chat": chat_id})

    conversations_serialized = ConversationSerializer(data=current_conversation, many=True)
    conversations_serialized.is_valid(raise_exception=True)
    conversations_serialized.save()


class StreamModelResponse(GenericAPIView):
    serializer_class = ChatConversationSerializer

    def get_queryset(self):
        """
        :return: 10 latest conversations
        """
        return Conversation.objects.filter(chat=self.kwargs["pk"]).order_by('-created_at')[:10]

    def post(self, request, **kwargs):
        if request.data["model"] in chat_completion_models + completion_models + fine_tunes:
            chat_history = self.get_serializer(self.get_queryset(), many=True).data
            current_conversation = [{
                "role": "user", "content": request.data["content"]
            }]

            return StreamingHttpResponse(
                stream_model_response(
                    model_id=request.data["model"],
                    chat_id=kwargs["pk"],
                    current_conversation=current_conversation,
                    chat_history=chat_history),
                content_type='text/event-stream')

        else:
            return Response({"error": f"The model: `{request.data['model']}` does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)
