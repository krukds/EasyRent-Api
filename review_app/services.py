from services.gpt_services import text_verification
from fastapi import HTTPException, status


async def verify_review_description(description):
    if description:
        verif_result = await text_verification(description)
        if not verif_result.is_ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ваш відгук не пройшов модерацію. Причина: {verif_result.reason_details or '-'}"
            )
    return True
