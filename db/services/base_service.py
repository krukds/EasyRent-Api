from typing import TypeVar, Generic, Type, List, Any

from sqlalchemy import select, func, update, insert, delete, Select, Update, Delete, Insert

T = TypeVar('T')


class BaseService(Generic[T]):
    session_maker: Type[T] = None
    model: Type[T] = None

    @classmethod
    async def execute(cls, query, commit: bool = False) -> Any:
        async with cls.session_maker() as session:
            result = await session.execute(query)

            if commit:
                await session.commit()

            if isinstance(query, Select):
                return result.unique().scalars().all()

            if isinstance(query, (Update, Delete, Insert)) and hasattr(query, "returning") and query.returning:
                return result.scalars().all()

            return result

    @classmethod
    async def select_one(cls, *filters, **filter_by):
        async with cls.session_maker() as session:
            stmt = select(cls.model)

            if filters:
                stmt = stmt.where(*filters)
            if filter_by:
                stmt = stmt.filter_by(**filter_by)

            result = await session.execute(stmt)
            return result.unique().scalar_one_or_none()

    @classmethod
    async def select_one_by_filters(cls, *args_filters, **kwargs_filters):
        async with cls.session_maker() as session:
            query = select(cls.model).where(*args_filters).filter_by(**kwargs_filters)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def select(cls, *args_filters, order_by=None, **filters) -> List[T]:
        async with cls.session_maker() as session:
            query = select(cls.model).where(*args_filters).filter_by(**filters)
            if order_by is not None:
                query = query.order_by(order_by)
            result = await session.execute(query)
            return result.scalars()

    @classmethod
    async def add(cls, **data) -> T:
        async with cls.session_maker() as session:
            obj = cls.model(**data)
            session.add(obj)
            await session.commit()
            return obj


    @classmethod
    async def save(cls, obj: T) -> T:
        async with cls.session_maker() as session:
            session.add(obj)
            await session.commit()
        return obj

    @classmethod
    async def update(cls, filters: dict, **data) -> bool:
        async with cls.session_maker() as session:
            query = update(cls.model).values(**data).filter_by(**filters)
            await session.execute(query)
            await session.commit()
            return True

    @classmethod
    async def update_by_id(cls, pk: int, **data) -> bool:
        return await cls.update({"id": pk}, **data)

    @classmethod
    async def delete(cls, *filters, **filter_by) -> bool:
        async with cls.session_maker() as session:
            stmt = delete(cls.model)

            if filters:
                stmt = stmt.where(*filters)

            if filter_by:
                stmt = stmt.filter_by(**filter_by)

            await session.execute(stmt)
            await session.commit()
            return True

    @classmethod
    async def count(cls, **filters):
        async with cls.session_maker() as session:
            query = select(func.count()).select_from(cls.model).filter_by(**filters)
            result = await session.execute(query)
            return result.scalar()
