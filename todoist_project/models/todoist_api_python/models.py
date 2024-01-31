from __future__ import annotations

from typing import List, Literal

import attr

from ..todoist_api_python.utils import get_url_for_task

VIEW_STYLE = Literal["list", "board"]


@attr.s
class Project(object):
    color: str = attr.ib()
    comment_count: int = attr.ib()
    id: str = attr.ib()
    is_favorite: bool = attr.ib()
    is_inbox_project: bool = attr.ib()
    is_shared: bool = attr.ib()
    is_team_inbox: bool = attr.ib()
    name: str = attr.ib()
    order: int = attr.ib()
    parent_id: str | None = attr.ib()
    url: str = attr.ib()
    view_style: VIEW_STYLE = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        return cls(
            color=obj["color"],
            comment_count=obj["comment_count"],
            id=obj["id"],
            is_favorite=obj["is_favorite"],
            is_inbox_project=obj.get("is_inbox_project"),
            is_shared=obj["is_shared"],
            is_team_inbox=obj.get("is_team_inbox"),
            name=obj["name"],
            order=obj.get("order"),
            parent_id=obj.get("parent_id"),
            url=obj["url"],
            view_style=obj["view_style"],
        )


@attr.s
class Section(object):
    id: str = attr.ib()
    name: str = attr.ib()
    order: int = attr.ib()
    project_id: str = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            name=obj["name"],
            order=obj["order"],
            project_id=obj["project_id"],
        )


@attr.s
class Due(object):
    date: str = attr.ib()
    is_recurring: bool = attr.ib()
    string: str = attr.ib()

    datetime: str | None = attr.ib(default=None)
    timezone: str | None = attr.ib(default=None)

    @classmethod
    def from_dict(cls, obj):
        return cls(
            date=obj["date"],
            is_recurring=obj["is_recurring"],
            string=obj["string"],
            datetime=obj.get("datetime"),
            timezone=obj.get("timezone"),
        )

    def to_dict(self):
        return {
            "date": self.date,
            "is_recurring": self.is_recurring,
            "string": self.string,
            "datetime": self.datetime,
            "timezone": self.timezone,
        }

    @classmethod
    def from_quick_add_response(cls, obj):
        due = obj.get("due")

        if not due:
            return None

        timezone = due.get("timezone")

        datetime: str | None = None

        if timezone:
            datetime = due["date"]

        return cls(
            date=due["date"],
            is_recurring=due["is_recurring"],
            string=due["string"],
            datetime=datetime,
            timezone=timezone,
        )


@attr.s
class Task(object):
    assignee_id: str | None = attr.ib()
    assigner_id: str | None = attr.ib()
    comment_count: int = attr.ib()
    is_completed: bool = attr.ib()
    content: str = attr.ib()
    created_at: str = attr.ib()
    creator_id: str = attr.ib()
    description: str = attr.ib()
    due: Due | None = attr.ib()
    id: str = attr.ib()
    labels: List[str] = attr.ib()
    order: int = attr.ib()
    parent_id: str | None = attr.ib()
    priority: int = attr.ib()
    project_id: str = attr.ib()
    section_id: str | None = attr.ib()
    url: str = attr.ib()

    sync_id: str | None = attr.ib(default=None)

    @classmethod
    def from_dict(cls, obj):
        due: Due | None = None

        if obj.get("due"):
            due = Due.from_dict(obj["due"])

        return cls(
            assignee_id=obj.get("assignee_id"),
            assigner_id=obj.get("assigner_id"),
            comment_count=obj["comment_count"],
            is_completed=obj["is_completed"],
            content=obj["content"],
            created_at=obj["created_at"],
            creator_id=obj["creator_id"],
            description=obj["description"],
            due=due,
            id=obj["id"],
            labels=obj.get("labels"),
            order=obj.get("order"),
            parent_id=obj.get("parent_id"),
            priority=obj["priority"],
            project_id=obj["project_id"],
            section_id=obj["section_id"],
            url=obj["url"],
        )

    def to_dict(self):
        due: dict | None = None

        if self.due:
            due = self.due.to_dict()

        return {
            "assignee_id": self.assignee_id,
            "assigner_id": self.assigner_id,
            "comment_count": self.comment_count,
            "is_completed": self.is_completed,
            "content": self.content,
            "created_at": self.created_at,
            "creator_id": self.creator_id,
            "description": self.description,
            "due": due,
            "id": self.id,
            "labels": self.labels,
            "order": self.order,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "project_id": self.project_id,
            "section_id": self.section_id,
            "sync_id": self.sync_id,
            "url": self.url,
        }

    @classmethod
    def from_quick_add_response(cls, obj):
        due: Due | None = None

        if obj.get("due"):
            due = Due.from_quick_add_response(obj)

        return cls(
            assignee_id=obj.get("responsible_uid"),
            assigner_id=obj.get("assigned_by_uid"),
            comment_count=0,
            is_completed=False,
            content=obj["content"],
            created_at=obj["added_at"],
            creator_id=obj["added_by_uid"],
            description=obj["description"],
            due=due,
            id=obj["id"],
            labels=obj["labels"],
            order=obj["child_order"],
            parent_id=obj["parent_id"] or None,
            priority=obj["priority"],
            project_id=obj["project_id"],
            section_id=obj["section_id"] or None,
            sync_id=obj["sync_id"],
            url=get_url_for_task(obj["id"], obj["sync_id"]),
        )


@attr.s
class QuickAddResult:
    task: Task = attr.ib()

    resolved_project_name: str | None = attr.ib(default=None)
    resolved_assignee_name: str | None = attr.ib(default=None)
    resolved_label_names: List[str] | None = attr.ib(default=None)
    resolved_section_name: str | None = attr.ib(default=None)

    @classmethod
    def from_quick_add_response(cls, obj):
        project_data = obj["meta"].get("project", {})
        assignee_data = obj["meta"].get("assignee", {})
        section_data = obj["meta"].get("section", {})

        resolved_project_name = None
        resolved_assignee_name = None
        resolved_section_name = None

        if project_data and len(project_data) == 2:
            resolved_project_name = obj["meta"]["project"][1]

        if assignee_data and len(assignee_data) == 2:
            resolved_assignee_name = obj["meta"]["assignee"][1]

        if section_data and len(section_data) == 2:
            resolved_section_name = obj["meta"]["section"][1]

        return cls(
            task=Task.from_quick_add_response(obj),
            resolved_project_name=resolved_project_name,
            resolved_assignee_name=resolved_assignee_name,
            resolved_label_names=list(obj["meta"]["labels"].values()),
            resolved_section_name=resolved_section_name,
        )


@attr.s
class Collaborator(object):
    id: str = attr.ib()
    email: str = attr.ib()
    name: str = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            email=obj["email"],
            name=obj["name"],
        )


@attr.s
class Attachment(object):
    resource_type: str | None = attr.ib(default=None)

    file_name: str | None = attr.ib(default=None)
    file_size: int | None = attr.ib(default=None)
    file_type: str | None = attr.ib(default=None)
    file_url: str | None = attr.ib(default=None)
    file_duration: int | None = attr.ib(default=None)
    upload_state: str | None = attr.ib(default=None)

    image: str | None = attr.ib(default=None)
    image_width: int | None = attr.ib(default=None)
    image_height: int | None = attr.ib(default=None)

    url: str | None = attr.ib(default=None)
    title: str | None = attr.ib(default=None)

    @classmethod
    def from_dict(cls, obj):
        return cls(
            resource_type=obj.get("resource_type"),
            file_name=obj.get("file_name"),
            file_size=obj.get("file_size"),
            file_type=obj.get("file_type"),
            file_url=obj.get("file_url"),
            upload_state=obj.get("upload_state"),
            image=obj.get("image"),
            image_width=obj.get("image_width"),
            image_height=obj.get("image_height"),
            url=obj.get("url"),
            title=obj.get("title"),
        )


@attr.s
class Comment(object):
    attachment: Attachment | None = attr.ib()
    content: str = attr.ib()
    id: str = attr.ib()
    posted_at: str = attr.ib()
    project_id: str | None = attr.ib()
    task_id: str | None = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        attachment: Attachment | None = None

        if "attachment" in obj and obj["attachment"] is not None:
            attachment = Attachment.from_dict(obj["attachment"])

        return cls(
            attachment=attachment,
            content=obj["content"],
            id=obj["id"],
            posted_at=obj["posted_at"],
            project_id=obj.get("project_id"),
            task_id=obj.get("task_id"),
        )


@attr.s
class Label:
    id: str = attr.ib()
    name: str = attr.ib()
    color: str = attr.ib()
    order: int = attr.ib()
    is_favorite: bool = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            name=obj["name"],
            color=obj["color"],
            order=obj["order"],
            is_favorite=obj["is_favorite"],
        )


@attr.s
class AuthResult:
    access_token: str = attr.ib()
    state: str = attr.ib()

    @classmethod
    def from_dict(cls, obj):
        return cls(
            access_token=obj["access_token"],
            state=obj["state"],
        )
