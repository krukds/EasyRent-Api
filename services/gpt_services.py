import json
import asyncio
import openai
from pydantic import BaseModel
from config import config

client = openai.AsyncOpenAI(
    api_key=config.API_KEY.get_secret_value(),
    organization=config.ORGANISATION_ID
)


class IdVerificationGptResult(BaseModel):
    image_quality: str = 'low'
    valid_data: bool = False
    first_name: str = ''
    second_name: str = ''
    patronymic: str = ''
    birth_date: str = ''
    error_details: str = ''
    is_front_side: bool = False


class TextVerificationGptResult(BaseModel):
    is_ok: bool = False
    valid_data: bool = False
    first_name: str = ''
    second_name: str = ''
    patronymic: str = ''
    birth_date: str = ''
    error_details: str = ''
    is_front_side: bool = False


async def passport_documents_verification(document_photos_paths: list[str]) -> IdVerificationGptResult:
    openai_document_ids = []
    for document_photo_path in document_photos_paths:
        with open(document_photo_path, "rb") as f:
            image_file = await client.files.create(
                file=f,
                purpose="assistants"
            )
            openai_document_ids.append(image_file.id)

    thread = await client.beta.threads.create()

    message_contents = [
        {
            "type": "text",
            "text": "Validate this passport and return json"
        }
    ]
    message_contents += [{
        "type": "image_file",
        "image_file": {"file_id": item}
    } for item in openai_document_ids]

    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_contents
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config.VERIFICATION_ASSISTANT_ID
    )

    while True:
        run_status = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        await asyncio.sleep(1)

    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            return IdVerificationGptResult(**json.loads(msg.content[0].text.value))

    return IdVerificationGptResult()


async def text_verification(text) -> IdVerificationGptResult:

    thread = await client.beta.threads.create()

    message_contents = [
        {
            "type": "text",
            "text": f"Input text: {text}"
        }
    ]

    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_contents
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config.VERIFICATION_ASSISTANT_ID
    )

    while True:
        run_status = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        await asyncio.sleep(1)

    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            return IdVerificationGptResult(**json.loads(msg.content[0].text.value))

    return IdVerificationGptResult()
