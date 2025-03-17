from __future__ import annotations as _annotations

import asyncio
import random
import uuid

from pydantic import BaseModel
from dotenv import load_dotenv

import os

from agents import (
    Agent,
    HandoffOutputItem,
    ItemHelpers,
    MessageOutputItem,
    RunContextWrapper,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    function_tool,
    handoff,
    trace,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# .envファイルから環境変数を読み込む
load_dotenv()

### コンテキスト

# AsyncOpenAIクライアントを初期化
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

# OpenAIChatCompletionsModelでクライアントをラップ
model = OpenAIChatCompletionsModel(
    model="xai/grok-2-latest",  # または他のモデル名
    openai_client=client,
)

class AirlineAgentContext(BaseModel):
    """航空会社エージェントのコンテキスト"""
    passenger_name: str | None = None    # 乗客名
    confirmation_number: str | None = None    # 予約番号
    seat_number: str | None = None    # 座席番号
    flight_number: str | None = None    # フライト番号


### ツール

@function_tool(
    name_override="faq_lookup_tool", description_override="よくある質問を検索します。"
)
async def faq_lookup_tool(question: str) -> str:
    """
    FAQを検索するツール
    """
    if "bag" in question or "baggage" in question:
        return (
            "機内に持ち込める手荷物は1個です。"
            "重量は22.7kg以下、サイズは56cm x 36cm x 23cm以下である必要があります。"
        )
    elif "seats" in question or "plane" in question:
        return (
            "機内の座席数は120席です。"
            "ビジネスクラスが22席、エコノミークラスが98席です。"
            "非常口座席は4列目と16列目です。"
            "5-8列目はレッグルームの広いエコノミープラスです。"
        )
    elif "wifi" in question:
        return "機内では無料Wi-Fiをご利用いただけます。「Airline-Wifi」に接続してください。"
    return "申し訳ありません。その質問についてはお答えできません。"


@function_tool
async def update_seat(
    context: RunContextWrapper[AirlineAgentContext], confirmation_number: str, new_seat: str
) -> str:
    """
    指定された予約番号の座席を更新します。

    Args:
        confirmation_number: 予約番号
        new_seat: 新しい座席番号
    """
    # コンテキストを更新
    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat
    # フライト番号が設定されていることを確認
    assert context.context.flight_number is not None, "フライト番号が必要です"
    return f"予約番号{confirmation_number}の座席を{new_seat}に変更しました"


### フック関数

async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    """座席予約エージェントへの引き継ぎ時に実行されるフック"""
    flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.flight_number = flight_number


### エージェント

faq_agent = Agent[AirlineAgentContext](
    name="FAQエージェント",
    handoff_description="航空会社に関する質問に答えるエージェントです。",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    あなたはFAQエージェントです。お客様と会話する場合、通常は振り分けエージェントから転送されています。
    以下の手順でお客様をサポートしてください。
    # 手順
    1. お客様の最後の質問を確認します。
    2. FAQ検索ツールを使用して質問に回答します。自身の知識に頼らないでください。
    3. 質問に回答できない場合は、振り分けエージェントに戻します。""",
    tools=[faq_lookup_tool],
    model=model,
)

seat_booking_agent = Agent[AirlineAgentContext](
    name="座席予約エージェント",
    handoff_description="フライトの座席を更新できるエージェントです。",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    あなたは座席予約エージェントです。お客様と会話する場合、通常は振り分けエージェントから転送されています。
    以下の手順でお客様をサポートしてください。
    # 手順
    1. 予約番号をお伺いします。
    2. ご希望の座席番号をお伺いします。
    3. 座席更新ツールを使用してフライトの座席を更新します。
    手順に関係のない質問があった場合は、振り分けエージェントに戻します。""",
    tools=[update_seat],
    model=model,
)

triage_agent = Agent[AirlineAgentContext](
    name="振り分けエージェント",
    handoff_description="お客様のご要望を適切なエージェントに振り分けるエージェントです。",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "あなたは親切な振り分けエージェントです。ツールを使用して質問を適切なエージェントに振り分けることができます。"
    ),
    handoffs=[
        faq_agent,
        handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),
    ],
    model=model,
)

faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)


### 実行

async def main():
    current_agent: Agent[AirlineAgentContext] = triage_agent
    input_items: list[TResponseInputItem] = []
    context = AirlineAgentContext()

    # 通常、ユーザーからの各入力はアプリへのAPIリクエストとなり、trace()でリクエストをラップできます
    # ここでは会話IDとしてランダムなUUIDを使用します
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input = input("メッセージを入力してください: ")

        input_items.append({"content": user_input, "role": "user"})
        result = await Runner.run(current_agent, input_items, context=context)

        for new_item in result.new_items:
            agent_name = new_item.agent.name
            if isinstance(new_item, MessageOutputItem):
                print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
            elif isinstance(new_item, HandoffOutputItem):
                print(
                    f"{new_item.source_agent.name}から{new_item.target_agent.name}に引き継ぎました"
                )
            elif isinstance(new_item, ToolCallItem):
                print(f"{agent_name}: ツールを呼び出しています")
            elif isinstance(new_item, ToolCallOutputItem):
                print(f"{agent_name}: ツール実行結果: {new_item.output}")
            else:
                print(f"{agent_name}: アイテムをスキップ: {new_item.__class__.__name__}")
        input_items = result.to_input_list()
        current_agent = result.last_agent


if __name__ == "__main__":
    asyncio.run(main())
