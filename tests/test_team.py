from pantheon.agent import Agent
from pantheon.team import SwarmTeam


async def test_swarm_team():
    scifi_fan = Agent(
        name="scifi_fan",
        instructions="You are a scifi fan. You like to read scifi books.",
    )
    romance_fan = Agent(
        name="romance_fan",
        instructions="You are a romance fan. You like to read romance books.",
    )

    @scifi_fan.tool
    def transfer_to_romance_fan():
        return romance_fan

    team = SwarmTeam([scifi_fan, romance_fan])
    resp = await team.run("Recommand me some romance books.")
    print(resp.content)
    assert resp.agent_name == "romance_fan"
