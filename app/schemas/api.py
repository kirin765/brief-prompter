from pydantic import BaseModel


class BriefRequest(BaseModel):
    dry_run: bool = False
