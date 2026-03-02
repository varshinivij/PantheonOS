import os

import pytest

from pantheon.agent import Agent
from pantheon.team import SwarmTeam

TEST_MODEL = os.getenv("PANTHEON_MODEL", "gpt-4o-mini")


async def test_swarm_team():
    scifi_fan = Agent(
        name="scifi_fan",
        instructions=(
            "You are a scifi fan. You ONLY answer questions about science fiction. "
            "For any other genre (romance, mystery, etc.), you MUST call "
            "transfer_to_romance_fan() immediately without answering."
        ),
        model=TEST_MODEL,
        model_params={"temperature": 0},
    )
    romance_fan = Agent(
        name="romance_fan",
        instructions="You are a romance fan. You like to read romance books.",
        model=TEST_MODEL,
        model_params={"temperature": 0},
    )

    @scifi_fan.tool
    def transfer_to_romance_fan():
        return romance_fan

    team = SwarmTeam([scifi_fan, romance_fan])
    resp = await team.run("Recommend me some romance books.")
    print(resp.content)
    assert resp.agent_name == "romance_fan"
