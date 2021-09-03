from dataclasses import dataclass


@dataclass
class Comment:
    by: str
    id: int
    time: int
    text: str
    kids: list
    deleted: bool
    dead: bool

@dataclass
class Story:
    by: str
    id: int
    score: int
    time: int
    title: str
    url: str
    comments: list[Comment]
