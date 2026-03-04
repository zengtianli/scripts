#!/usr/bin/env python3
"""
项目管理系统 - SQLite 数据库操作
用于管理工作和个人项目的元数据
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class ProjectManager:
    """项目管理器"""

    def __init__(self, db_path: str = "~/Library/Logs/secretary/projects.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建 projects 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    current_task TEXT,
                    blocked_reason TEXT,
                    next_steps TEXT,
                    md_file TEXT,
                    tags TEXT
                )
            """)

            # 创建 project_history 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    notes TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_type
                ON projects(type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_status
                ON projects(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_project_id
                ON project_history(project_id)
            """)

            conn.commit()

    def create_project(
        self,
        project_id: str,
        name: str,
        project_type: str,
        status: str = "todo",
        priority: Optional[str] = None,
        current_task: Optional[str] = None,
        blocked_reason: Optional[str] = None,
        next_steps: Optional[str] = None,
        md_file: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建新项目

        Args:
            project_id: 项目 ID
            name: 项目名称
            project_type: 项目类型 (work/personal)
            status: 项目状态 (todo/in_progress/blocked/done)
            priority: 优先级 (high/medium/low)
            current_task: 当前任务
            blocked_reason: 卡住原因
            next_steps: 下一步计划
            md_file: Markdown 文件路径
            tags: 标签列表

        Returns:
            创建的项目数据
        """
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO projects (
                    id, name, type, status, priority, created_at, updated_at,
                    current_task, blocked_reason, next_steps, md_file, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id, name, project_type, status, priority, now, now,
                current_task, blocked_reason, next_steps, md_file, tags_json
            ))

            # 添加历史记录
            self._add_history(
                cursor, project_id, "created", None, status,
                f"创建项目: {name}"
            )

            conn.commit()

        return self.get_project(project_id)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目详情"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()

            if row:
                project = dict(row)
                project['tags'] = json.loads(project['tags'])
                return project
            return None

    def update_project(
        self,
        project_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        更新项目

        Args:
            project_id: 项目 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的项目数据
        """
        # 获取当前项目数据
        old_project = self.get_project(project_id)
        if not old_project:
            return None

        # 准备更新字段
        allowed_fields = {
            'name', 'type', 'status', 'priority', 'current_task',
            'blocked_reason', 'next_steps', 'md_file', 'tags'
        }
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return old_project

        # 处理 tags
        if 'tags' in update_fields:
            update_fields['tags'] = json.dumps(update_fields['tags'])

        # 更新 updated_at
        update_fields['updated_at'] = datetime.now().isoformat()

        # 构建 SQL
        set_clause = ', '.join(f"{k} = ?" for k in update_fields.keys())
        values = list(update_fields.values()) + [project_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?",
                values
            )

            # 添加历史记录
            for field, new_value in kwargs.items():
                if field in allowed_fields:
                    old_value = old_project.get(field)
                    if old_value != new_value:
                        action = "status_changed" if field == "status" else "updated"
                        self._add_history(
                            cursor, project_id, action,
                            str(old_value), str(new_value),
                            f"更新 {field}: {old_value} -> {new_value}"
                        )

            conn.commit()

        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 删除历史记录
            cursor.execute(
                "DELETE FROM project_history WHERE project_id = ?",
                (project_id,)
            )

            # 删除项目
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

            conn.commit()
            return cursor.rowcount > 0

    def list_projects(
        self,
        project_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出项目

        Args:
            project_type: 过滤项目类型 (work/personal)
            status: 过滤状态 (todo/in_progress/blocked/done)
            priority: 过滤优先级 (high/medium/low)

        Returns:
            项目列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM projects WHERE 1=1"
            params = []

            if project_type:
                query += " AND type = ?"
                params.append(project_type)

            if status:
                query += " AND status = ?"
                params.append(status)

            if priority:
                query += " AND priority = ?"
                params.append(priority)

            query += " ORDER BY updated_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            projects = []
            for row in rows:
                project = dict(row)
                project['tags'] = json.loads(project['tags'])
                projects.append(project)

            return projects

    def get_history(
        self,
        project_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取项目历史记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT * FROM project_history
                WHERE project_id = ?
                ORDER BY timestamp DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def _add_history(
        self,
        cursor: sqlite3.Cursor,
        project_id: str,
        action: str,
        old_value: Optional[str],
        new_value: Optional[str],
        notes: Optional[str]
    ):
        """添加历史记录（内部方法）"""
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO project_history (
                project_id, timestamp, action, old_value, new_value, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, timestamp, action, old_value, new_value, notes))


def main():
    """测试函数"""
    pm = ProjectManager()

    print("=== 项目管理系统测试 ===\n")

    # 测试 1: 创建工作项目
    print("1. 创建工作项目...")
    work_project = pm.create_project(
        project_id="work-system-refactor",
        name="XX系统重构",
        project_type="work",
        status="in_progress",
        priority="high",
        current_task="完成需求文档",
        next_steps="等待产品经理确认",
        tags=["系统重构", "需求分析"]
    )
    print(f"   ✓ 创建成功: {work_project['name']}")

    # 测试 2: 创建个人项目
    print("\n2. 创建个人项目...")
    personal_project = pm.create_project(
        project_id="personal-ai-learning",
        name="AI 应用开发学习",
        project_type="personal",
        status="in_progress",
        priority="medium",
        current_task="学习 LangChain",
        tags=["学习", "AI"]
    )
    print(f"   ✓ 创建成功: {personal_project['name']}")

    # 测试 3: 更新项目状态
    print("\n3. 更新项目状态...")
    updated = pm.update_project(
        "work-system-refactor",
        status="blocked",
        blocked_reason="等待产品经理确认需求"
    )
    print(f"   ✓ 状态更新: {updated['status']}")

    # 测试 4: 列出所有项目
    print("\n4. 列出所有项目...")
    all_projects = pm.list_projects()
    for p in all_projects:
        print(f"   - [{p['type']}] {p['name']} ({p['status']})")

    # 测试 5: 列出进行中的项目
    print("\n5. 列出进行中的项目...")
    in_progress = pm.list_projects(status="in_progress")
    print(f"   ✓ 找到 {len(in_progress)} 个进行中的项目")

    # 测试 6: 查看历史记录
    print("\n6. 查看项目历史...")
    history = pm.get_history("work-system-refactor")
    for h in history:
        print(f"   - [{h['action']}] {h['notes']}")

    # 测试 7: 删除项目
    print("\n7. 删除测试项目...")
    pm.delete_project("work-system-refactor")
    pm.delete_project("personal-ai-learning")
    print("   ✓ 测试项目已清理")

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
