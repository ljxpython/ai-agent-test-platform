"""
数据库模型和连接配置
使用SQLite存储文档元数据
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 数据库文件路径
DB_PATH = Path(__file__).parent / "knowledge_base.db"


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 创建文档表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'uploaded',
                chunk_count INTEGER DEFAULT 0,
                description TEXT,
                tags TEXT
            )
        """
        )

        # 创建文档块表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                vector_id TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """
        )

        # 创建索引
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_document_id
            ON document_chunks(document_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_status
            ON documents(status)
        """
        )

        conn.commit()


class DocumentDB:
    """文档数据库操作类"""

    @staticmethod
    def create_document(
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        description: str = None,
        tags: str = None,
    ) -> int:
        """创建文档记录"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents
                (filename, original_filename, file_path, file_size, file_type, description, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    filename,
                    original_filename,
                    file_path,
                    file_size,
                    file_type,
                    description,
                    tags,
                ),
            )
            return cursor.lastrowid

    @staticmethod
    def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_documents(
        page: int = 1, page_size: int = 10, status: str = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取文档列表"""
        offset = (page - 1) * page_size

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 构建查询条件
            where_clause = "WHERE status = ?" if status else ""
            params = [status] if status else []

            # 获取总数
            cursor.execute(f"SELECT COUNT(*) FROM documents {where_clause}", params)
            total = cursor.fetchone()[0]

            # 获取分页数据
            cursor.execute(
                f"""
                SELECT * FROM documents {where_clause}
                ORDER BY upload_time DESC
                LIMIT ? OFFSET ?
            """,
                params + [page_size, offset],
            )

            documents = [dict(row) for row in cursor.fetchall()]
            return documents, total

    @staticmethod
    def update_document_status(doc_id: int, status: str, chunk_count: int = None):
        """更新文档状态"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if chunk_count is not None:
                cursor.execute(
                    """
                    UPDATE documents
                    SET status = ?, chunk_count = ?
                    WHERE id = ?
                """,
                    (status, chunk_count, doc_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE documents
                    SET status = ?
                    WHERE id = ?
                """,
                    (status, doc_id),
                )

    @staticmethod
    def delete_document(doc_id: int):
        """删除文档"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
