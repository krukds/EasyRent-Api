from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import datetime
from sqlalchemy import func
from db.models import ListingModel
from db.services.main_services import ListingService, UserService
from listing_app.schemes import ARCHIVED_STATUS_ID, ACTIVE_STATUS_ID
from services.mailing import send_email_async


async def worker_checking_listing_relevance():
    print(f"[{datetime.datetime.now()}] worker_checking_listing_relevance запущений")
    now = datetime.datetime.utcnow()
    listings = await ListingService.select(
        func.date(ListingModel.created_at) == (now - datetime.timedelta(days=15)).date(),
        listing_status_id=ACTIVE_STATUS_ID
    )
    # print((now - datetime.timedelta(days=15)).date())
    for listing in listings:
        # print(listing)
        user = await UserService.select_one(id=listing.owner_id)
        if not user:
            continue

        text = f"""
Шановний(а) користувачу,

Повідомляємо, що ваше оголошення "{listing.name}" було автоматично переміщене до розділу «Архівовані» у зв’язку з відсутністю активності протягом останніх 15 днів.

Відповідно до правил платформи, оголошення, які не оновлювались або не мали активних дій упродовж зазначеного періоду, автоматично архівуються з метою забезпечення актуальності контенту.

У разі потреби ви можете повторно активувати оголошення у своєму особистому кабінеті.

З повагою,
Команда EasyRent
        """
        await send_email_async(
            user.email,
            subject="EasyRent - повідомлення про архівацію оголошення",
            body=text
        )
        listing.listing_status_id = ARCHIVED_STATUS_ID
        await ListingService.save(listing)



def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(worker_checking_listing_relevance, CronTrigger(hour=12, minute=0))
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
    asyncio.get_event_loop().run_forever()
