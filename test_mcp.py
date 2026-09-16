import asyncio
import mcp_server


async def main():
    tools = await mcp_server.server.list_tools()
    print("Tools:")
    for t in tools:
        print("-", t.name)


asyncio.run(main())
