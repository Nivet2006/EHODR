import asyncio
from qdrant_client import AsyncQdrantClient

async def check():
    client = AsyncQdrantClient(host='localhost', port=6333)
    try:
        count = await client.count('ai_memories')
        print(f"POINTS_COUNT: {count.count}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await client.close()

if __name__ == '__main__':
    asyncio.run(check())
