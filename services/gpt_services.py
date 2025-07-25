import asyncio
import json

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
    reason_details: str = ''


class OwnershipVerificationGptResult(BaseModel):
    valid: bool = False
    belongs_to_user: bool = False
    error_details: str = ''


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
        await asyncio.sleep(0.2)

    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            result_text = msg.content[0].text.value
            return IdVerificationGptResult(**json.loads(
                result_text.replace("json", "").replace("`", "")
            ))

    return IdVerificationGptResult()


async def ownership_documents_verification(
        owner_first_name: str,
        owner_second_name: str,
        owner_patronymic: str,
        owner_birth_date: str,
        document_ownership_path: str,
        city: str,
        street: str,
) -> OwnershipVerificationGptResult:
    openai_document_ids = []
    with open(document_ownership_path, "rb") as f:
        # try:
        image_file = await client.files.create(
            file=f,
            purpose="assistants"
        )
        # except Exception as e:
        #     return OwnershipVerificationGptResult(error_details=str(e))
        openai_document_ids.append(image_file.id)

    thread = await client.beta.threads.create()
    # thread = await client.beta.threads.retrieve("thread_JA6FSQomLZ06ZhtVRHk8kZxT")

    message_contents = []
    message_contents.append(
        {
            "type": "text",
            "text": f"{owner_first_name} {owner_second_name} {owner_patronymic}\n"
                    f"City: {city}, {street}\n"
        }
    )
    message_contents += [{
        "type": "image_file",
        "image_file": {"file_id": item}
    } for item in openai_document_ids]
    print(message_contents)
    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_contents
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config.OWNERSHIP_VERIFICATION_ASSISTANT_ID
    )

    while True:
        run_status = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        await asyncio.sleep(0.2)

    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            result_text = msg.content[0].text.value
            return OwnershipVerificationGptResult(**json.loads(
                result_text.replace("json", "").replace("`", "")
            ))

    return OwnershipVerificationGptResult()


async def text_and_image_verification(
        text: str,
        image_paths=None
) -> TextVerificationGptResult:
    if image_paths is None:
        image_paths = []

    openai_document_ids = []
    for image_path in image_paths:
        with open(image_path, "rb") as f:
            image_file = await client.files.create(
                file=f,
                purpose="assistants"
            )
            openai_document_ids.append(image_file.id)

    thread = await client.beta.threads.create()

    message_contents = [
        {
            "type": "text",
            "text": f"Input text: {text}"
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
        assistant_id=config.MODERATOR_ASSISTANT_ID
    )

    while True:
        run_status = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        await asyncio.sleep(0.2)

    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    for msg in reversed(messages.data):
        if msg.role == "assistant":
            result_text = msg.content[0].text.value
            return TextVerificationGptResult(**json.loads(
                result_text.replace("json", "").replace("`", "")
            ))

    return TextVerificationGptResult()
