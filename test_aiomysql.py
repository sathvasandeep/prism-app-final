import asyncio
import aiomysql

async def test_conn():
    conn = await aiomysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
        db='prism_db'
    )
    async with conn.cursor() as cur:
        await cur.execute("SELECT * FROM professions LIMIT 5;")
        result = await cur.fetchall()
        print(result)
    conn.close()

asyncio.run(test_conn())