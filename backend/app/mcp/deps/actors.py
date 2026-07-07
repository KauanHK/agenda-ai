from typing import Annotated

from fastmcp import Context
from fastmcp.dependencies import Depends

from app.core.actors.user import CustomerActor


async def get_actor(ctx: Context) -> CustomerActor:
    return await ctx.get_state("actor")


ActorDep = Annotated[CustomerActor, Depends(get_actor)]
