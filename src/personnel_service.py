from __future__ import annotations

from typing import Any

from .db import DB_PATH, connect, initialize


class PersonnelService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        initialize(self.db_path)

    def search(
        self,
        query: str = "",
        camp: str = "",
        office: str = "",
        rank: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions = []
        params: dict[str, Any] = {"limit": max(1, min(int(limit), 500))}

        query = (query or "").strip()
        if query:
            params["query"] = f"%{query}%"
            conditions.append(
                "("
                "badge_number LIKE :query OR "
                "rank LIKE :query OR "
                "last_name LIKE :query OR "
                "first_name LIKE :query OR "
                "middle_name LIKE :query OR "
                "TRIM(COALESCE(first_name,'') || ' ' || COALESCE(middle_name,'') || ' ' || COALESCE(last_name,'')) LIKE :query"
                ")"
            )

        for field, value in (("camp", camp), ("office", office), ("rank", rank)):
            value = (value or "").strip()
            if value:
                params[field] = value
                conditions.append(f"{field} = :{field}")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT badge_number, rank, last_name, first_name, middle_name, suffix,
                   camp, office, gender, classification, personnel_type
            FROM personnel
            {where}
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
            LIMIT :limit
        """

        with connect(self.db_path) as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def get_profile(self, badge_number: str) -> dict[str, Any] | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM personnel WHERE badge_number = ?",
                (str(badge_number),),
            ).fetchone()
        return dict(row) if row else None

    def filters(self) -> dict[str, list[str]]:
        with connect(self.db_path) as connection:
            result = {}
            for field in ("camp", "office", "rank"):
                rows = connection.execute(
                    f"SELECT DISTINCT {field} FROM personnel "
                    f"WHERE {field} IS NOT NULL AND TRIM({field}) <> '' "
                    f"ORDER BY {field} COLLATE NOCASE"
                ).fetchall()
                result[field] = [row[0] for row in rows]
        return result

    def stats(self) -> dict[str, int]:
        with connect(self.db_path) as connection:
            total = connection.execute("SELECT COUNT(*) FROM personnel").fetchone()[0]
        return {"total": total}
