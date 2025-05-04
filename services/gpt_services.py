import json

import openai
import time

ORGANISATION_ID = "org-X8cLtCtPJakIJXwKaQIm7BKe"
API_KEY = "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"
VERIFICATION_ASSISTANT_ID = "asst_RKvextCvANlRLmxkhdSKvujK"
openai.api_key = API_KEY


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
        assistant_id=VERIFICATION_ASSISTANT_ID
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