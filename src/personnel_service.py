from __future__ import annotations

from typing import Any

from .db import DB_PATH, connect, initialize


class PersonnelService:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        initialize(self.db_path)

    def _search_one(
        self,
        query: str,
        camp: str,
        office: str,
        rank: str,
        limit: int,
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
                "TRIM(COALESCE(first_name,'') || ' ' || COALESCE(middle_name,'') || ' ' || COALESCE(last_name,'')) LIKE :query OR "
                "TRIM(COALESCE(last_name,'') || ' ' || COALESCE(first_name,'') || ' ' || COALESCE(middle_name,'')) LIKE :query"
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
                   camp, office, gender, classification, personnel_type, source_order
            FROM personnel
            {where}
            ORDER BY
                CASE WHEN source_order IS NULL THEN 1 ELSE 0 END,
                source_order,
                rowid
            LIMIT :limit
        """

        with connect(self.db_path) as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def search(
        self,
        query: str = "",
        camp: str = "",
        office: str = "",
        rank: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        max_results = max(1, min(int(limit), 500))
        terms = [line.strip() for line in (query or "").splitlines() if line.strip()]

        if not terms:
            return self._search_one("", camp, office, rank, max_results)

        results: list[dict[str, Any]] = []
        seen_badges: set[str] = set()

        for term in terms:
            remaining = max_results - len(results)
            if remaining <= 0:
                break

            matches = self._search_one(term, camp, office, rank, remaining)
            for person in matches:
                badge = str(person.get("badge_number") or "")
                if badge in seen_badges:
                    continue
                seen_badges.add(badge)
                results.append(person)
                if len(results) >= max_results:
                    break

        return results

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
