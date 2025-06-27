
import asyncio
import aiohttp

async def test_health():
    """Test health check endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://0.0.0.0:5000/health', timeout=5) as response:
                data = await response.json()
                print(f"Health check: {response.status} - {data}")
                return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_health())
    print(f"Health check {'PASSED' if result else 'FAILED'}")
