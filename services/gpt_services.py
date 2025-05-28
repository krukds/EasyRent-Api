import json

import openai
import time

from config import config

openai.organization = config.ORGANISATION_ID
openai.api_key = config.API_KEY.get_secret_value()

def passport_documents_verification(document_photos_paths: list[str]) -> dict:
    openai_document_ids = []
    for document_photo_path in document_photos_paths:
        image_file = openai.files.create(
            file=open(document_photo_path, "rb"),
            purpose="assistants"
        )
        openai_document_ids.append(
            image_file.id
        )

    thread = openai.beta.threads.create()

    message_contents = [
        {
            "type": "text",
            "text": "Перевір чи валідний паспорт"
        }
    ]
    message_contents += [{"type":"image_file",
                          "image_file": {"file_id": item}} for item in openai_document_ids]

    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_contents
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config.VERIFICATION_ASSISTANT_ID
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)

    passport_data = {}
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            passport_data = json.loads(msg.content[0].text.value)
    return passport_data


if __name__ == '__main__':
    res = passport_documents_verification([
        "../TEST/id_front_side.jpg",
        "../TEST/id_back_side.jpg",
    ])
    # res = passport_documents_verification([
    #     "../TEST/student_id.jpg",
    # ])
    print(res)