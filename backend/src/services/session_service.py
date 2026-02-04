import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.session_model import SessionModel, SessionCreate, SessionUpdate
from src.services.database_service import database_service
import uuid

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionService:
    def create_session(self, session_data: SessionCreate) -> SessionModel:
        try:
            session_id = session_data.session_id if session_data.session_id else str(uuid.uuid4())
            created_at = datetime.now()
            last_active = created_at
            conversation = session_data.conversation if session_data.conversation else []
            
            # 插入数据库
            query = """
            INSERT INTO query_sessions (session_id, user_id, conversation, last_active, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                session_id,
                session_data.user_id,
                json.dumps([msg.dict() for msg in conversation]),
                last_active,
                created_at
            )
            
            database_service.execute_query(query, params)
            
            # 返回创建的会话对象
            return SessionModel(
                id=None,
                user_id=session_data.user_id,
                session_id=session_id,
                conversation=conversation,
                last_active=last_active,
                created_at=created_at
            )
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise

    def get_all_sessions(self, user_id: Optional[int] = None) -> List[SessionModel]:
        try:
            if user_id is not None:
                query = """
                SELECT id, user_id, session_id, conversation, last_active, created_at
                FROM query_sessions 
                WHERE user_id = %s 
                ORDER BY last_active DESC
                """
                params = (user_id,)
            else:
                query = """
                SELECT id, user_id, session_id, conversation, last_active, created_at
                FROM query_sessions 
                ORDER BY last_active DESC
                """
                params = ()
            
            rows = database_service.fetch_all(query, params)
            
            sessions = []
            for row in rows:
                conversation = json.loads(row[3]) if row[3] else []
                sessions.append(SessionModel(
                    id=row[0],
                    user_id=row[1],
                    session_id=row[2],
                    conversation=conversation,
                    last_active=row[4],
                    created_at=row[5]
                ))
            
            return sessions
        except Exception as e:
            logger.error(f"Error fetching all sessions: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        try:
            query = """
            SELECT id, user_id, session_id, conversation, last_active, created_at
            FROM query_sessions 
            WHERE session_id = %s
            """
            params = (session_id,)
            
            row = database_service.fetch_one(query, params)
            
            if not row:
                return None
            
            conversation = json.loads(row[3]) if row[3] else []
            
            return SessionModel(
                id=row[0],
                user_id=row[1],
                session_id=row[2],
                conversation=conversation,
                last_active=row[4],
                created_at=row[5]
            )
        except Exception as e:
            logger.error(f"Error fetching session {session_id}: {str(e)}")
            raise

    def update_session(self, session_id: str, updates: SessionUpdate) -> Optional[SessionModel]:
        try:
            # 只允许更新名称和用户ID
            if not updates.name and not updates.user_id:
                return None
            
            last_active = datetime.now()
            
            # 构建动态更新语句
            set_clauses = []
            params = []
            
            if updates.name:
                set_clauses.append("name = %s")
                params.append(updates.name)
            
            if updates.user_id:
                set_clauses.append("user_id = %s")
                params.append(updates.user_id)
            
            set_clauses.append("last_active = %s")
            params.append(last_active)
            
            set_clause = ", ".join(set_clauses)
            
            query = f"""
            UPDATE query_sessions 
            SET {set_clause}
            WHERE session_id = %s
            """
            params.append(session_id)
            
            affected_rows = database_service.execute_query(query, params)
            
            if affected_rows == 0:
                return None
            
            # 返回更新后的会话
            return self.get_session(session_id)
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            raise

    def delete_session(self, session_id: str) -> bool:
        try:
            query = """
            DELETE FROM query_sessions 
            WHERE session_id = %s
            """
            params = (session_id,)
            
            affected_rows = database_service.execute_query(query, params)
            
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise

    def add_message_to_session(self, session_id: str, role: str, content: str) -> bool:
        try:
            # 获取当前会话
            session = self.get_session(session_id)
            if not session:
                return False
            
            # 构造新消息
            new_message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            # 更新对话历史
            conversation = session.conversation.copy()
            conversation.append(new_message)
            
            # 更新数据库
            last_active = datetime.now()
            query = """
            UPDATE query_sessions 
            SET conversation = %s, last_active = %s
            WHERE session_id = %s
            """
            params = (json.dumps(conversation), last_active, session_id)
            
            affected_rows = database_service.execute_query(query, params)
            
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {str(e)}")
            raise

# 创建全局实例
session_service = SessionService()