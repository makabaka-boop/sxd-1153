from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
from backend.app.models import Knowledge, Category, User, ReadingStatus
from backend.app.schemas import KnowledgeCreate, KnowledgeUpdate


class KnowledgeService:
    @staticmethod
    def get_knowledge_list(
        db: Session,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[int] = None,
        review_status: Optional[str] = None,
        keyword: Optional[str] = None
    ):
        query = db.query(Knowledge).filter(Knowledge.review_status != 'rejected')
        
        if category_id is not None:
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                query = query.join(Category).filter(
                    (Category.id == category_id) | 
                    (Category.path.like(f"{category.path}/%"))
                )
        
        if review_status:
            query = query.filter(Knowledge.review_status == review_status)
        
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                (Knowledge.title.like(keyword_pattern)) |
                (Knowledge.content.like(keyword_pattern))
            )
        
        total = query.count()
        items = query.order_by(Knowledge.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            is_read = None
            if user_id:
                reading = db.query(ReadingStatus).filter(
                    ReadingStatus.knowledge_id == item.id,
                    ReadingStatus.user_id == user_id
                ).first()
                is_read = reading is not None and reading.is_read
            
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "is_read": is_read,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_knowledge_by_id(db: Session, knowledge_id: int, user_id: Optional[int] = None):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识条目不存在"
            )
        
        is_read = None
        if user_id:
            reading = db.query(ReadingStatus).filter(
                ReadingStatus.knowledge_id == knowledge_id,
                ReadingStatus.user_id == user_id
            ).first()
            is_read = reading is not None and reading.is_read
        
        return {
            "id": knowledge.id,
            "title": knowledge.title,
            "content": knowledge.content,
            "category_id": knowledge.category_id,
            "category_name": knowledge.category.name if knowledge.category else None,
            "submitter_id": knowledge.submitter_id,
            "submitter_name": knowledge.submitter.name if knowledge.submitter else None,
            "review_status": knowledge.review_status,
            "reject_reason": knowledge.reject_reason,
            "is_read": is_read,
            "created_at": knowledge.created_at,
            "updated_at": knowledge.updated_at
        }

    @staticmethod
    def create_knowledge(db: Session, knowledge_data: KnowledgeCreate, submitter_id: int):
        category = db.query(Category).filter(Category.id == knowledge_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )
        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分类已停用"
            )
        
        db_knowledge = Knowledge(
            title=knowledge_data.title,
            content=knowledge_data.content,
            category_id=knowledge_data.category_id,
            submitter_id=submitter_id,
            review_status="pending"
        )
        db.add(db_knowledge)
        db.commit()
        db.refresh(db_knowledge)
        return db_knowledge

    @staticmethod
    def update_knowledge(db: Session, knowledge_id: int, knowledge_data: KnowledgeUpdate, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识条目不存在"
            )
        
        if knowledge.submitter_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能编辑自己提交的知识条目"
            )
        
        if knowledge_data.title is not None:
            knowledge.title = knowledge_data.title
        if knowledge_data.content is not None:
            knowledge.content = knowledge_data.content
        if knowledge_data.category_id is not None:
            category = db.query(Category).filter(Category.id == knowledge_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分类不存在"
                )
            if not category.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该分类已停用"
                )
            knowledge.category_id = knowledge_data.category_id
        
        knowledge.review_status = "pending"
        knowledge.reject_reason = None
        
        db.commit()
        db.refresh(knowledge)
        return knowledge

    @staticmethod
    def delete_knowledge(db: Session, knowledge_id: int, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识条目不存在"
            )
        
        if knowledge.submitter_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能删除自己提交的知识条目"
            )
        
        db.query(ReadingStatus).filter(ReadingStatus.knowledge_id == knowledge_id).delete()
        
        db.delete(knowledge)
        db.commit()

    @staticmethod
    def get_my_knowledge(db: Session, submitter_id: int, page: int = 1, page_size: int = 10):
        query = db.query(Knowledge).filter(Knowledge.submitter_id == submitter_id)
        total = query.count()
        items = query.order_by(Knowledge.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "is_read": None,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_all_for_export(db: Session, category_id: Optional[int] = None, review_status: Optional[str] = None):
        query = db.query(Knowledge).filter(Knowledge.review_status != 'rejected')
        
        if category_id is not None:
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                query = query.join(Category).filter(
                    (Category.id == category_id) | 
                    (Category.path.like(f"{category.path}/%"))
                )
        
        if review_status:
            query = query.filter(Knowledge.review_status == review_status)
        
        items = query.order_by(Knowledge.created_at.desc()).all()
        
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return result
