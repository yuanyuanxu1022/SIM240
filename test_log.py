import asyncio
import mcp_server


async def main():
    result = mcp_server.read_latest_log()
    print(result[:1000])


asyncio.run(main())
