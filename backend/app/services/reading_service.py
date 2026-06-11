from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from backend.app.models import ReadingStatus, Knowledge


class ReadingService:
    @staticmethod
    def mark_as_read(db: Session, knowledge_id: int, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识条目不存在"
            )
        
        existing = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == knowledge_id,
            ReadingStatus.user_id == user_id
        ).first()
        
        if existing:
            existing.is_read = True
            existing.read_at = datetime.now()
        else:
            reading = ReadingStatus(
                knowledge_id=knowledge_id,
                user_id=user_id,
                is_read=True,
                read_at=datetime.now()
            )
            db.add(reading)
        
        db.commit()
        return {"message": "标记已读成功"}

    @staticmethod
    def mark_as_unread(db: Session, knowledge_id: int, user_id: int):
        reading = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == knowledge_id,
            ReadingStatus.user_id == user_id
        ).first()
        
        if reading:
            db.delete(reading)
            db.commit()
        
        return {"message": "标记未读成功"}

    @staticmethod
    def get_my_reading_status(db: Session, user_id: int, page: int = 1, page_size: int = 10):
        query = db.query(ReadingStatus).filter(
            ReadingStatus.user_id == user_id,
            ReadingStatus.is_read == True
        )
        
        total = query.count()
        items = query.order_by(ReadingStatus.read_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "knowledge_id": item.knowledge_id,
                "knowledge_title": item.knowledge.title if item.knowledge else None,
                "user_id": item.user_id,
                "is_read": item.is_read,
                "read_at": item.read_at
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
