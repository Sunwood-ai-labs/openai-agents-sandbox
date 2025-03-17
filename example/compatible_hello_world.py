import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# .envファイルから環境変数を読み込む
load_dotenv()

async def main():
    # AsyncOpenAIクライアントを初期化
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )

    # OpenAIChatCompletionsModelでクライアントをラップ
    model = OpenAIChatCompletionsModel(
        model="bedrock/converse/us.deepseek.r1-v1:0",  # または他のモデル名
        openai_client=client,
    )

    # Agentの作成時にmodelパラメータを指定
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
        model=model,
    )

    result = await Runner.run(agent, "Tell me about recursion in programming.")
    print("-----------------------------")
    print(result.final_output)
    # Function calls itself,
    # Looping in smaller pieces,
    # Endless by design.


if __name__ == "__main__":
    asyncio.run(main())
