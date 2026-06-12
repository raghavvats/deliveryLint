from typing import Annotated

from pydantic import Field

AuthorityLevel = Annotated[int, Field(ge=1, le=5)]
