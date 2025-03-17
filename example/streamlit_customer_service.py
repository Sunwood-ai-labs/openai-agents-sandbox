import streamlit as st
import asyncio
from compatible_customer_service_jp import (
    triage_agent,
    AirlineAgentContext,
    Runner,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    ItemHelpers,
)

st.set_page_config(
    page_title="航空会社カスタマーサービス",
    page_icon="✈️",
)

# エージェントごとのアイコンを定義
AGENT_ICONS = {
    "振り分けエージェント": "🎯",  # 振り分けを表す的のアイコン
    "FAQエージェント": "📚",      # 情報・知識を表す本のアイコン
    "座席予約エージェント": "💺",  # 座席を表すアイコン
}

st.title("✈️ 航空会社カスタマーサービス")

# セッションステートの初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.input_items = []
    st.session_state.context = AirlineAgentContext()
    st.session_state.current_agent = triage_agent

    # 初期メッセージを追加
    welcome_message = {
        "role": "assistant",
        "agent": "振り分けエージェント",
        "content": "いらっしゃいませ！ご用件をお聞かせください。"
    }
    st.session_state.messages.append(welcome_message)

# チャット履歴の表示
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message["content"])
    else:
        # エージェントのアイコンを取得（デフォルトは✨）
        agent_icon = AGENT_ICONS.get(message.get("agent", ""), "✨")
        with st.chat_message("assistant", avatar=agent_icon):
            st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください"):
    # ユーザーのメッセージを表示
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # エージェントの入力アイテムを更新
    st.session_state.input_items.append({"content": prompt, "role": "user"})

    # エージェントの応答を取得
    responses = []
    with st.spinner("考え中..."):
        # 非同期関数を実行
        result = asyncio.run(
            Runner.run(
                st.session_state.current_agent,
                st.session_state.input_items,
                context=st.session_state.context
            )
        )

        # 結果を処理
        current_agent_name = None
        current_responses = []

        for new_item in result.new_items:
            agent_name = new_item.agent.name
            
            if isinstance(new_item, MessageOutputItem):
                response = ItemHelpers.text_message_output(new_item)
                if current_agent_name and current_agent_name != agent_name:
                    # 前のエージェントの応答をまとめて表示
                    responses.append({"agent": current_agent_name, "content": "\n\n".join(current_responses)})
                    current_responses = []
                current_agent_name = agent_name
                current_responses.append(response)
            elif isinstance(new_item, HandoffOutputItem):
                response = f"{new_item.source_agent.name}から{new_item.target_agent.name}に引き継ぎました"
                responses.append({"agent": new_item.source_agent.name, "content": response})
            elif isinstance(new_item, ToolCallItem):
                response = f"ツールを呼び出しています"
                if current_agent_name and current_agent_name != agent_name:
                    responses.append({"agent": current_agent_name, "content": "\n\n".join(current_responses)})
                    current_responses = []
                current_agent_name = agent_name
                current_responses.append(response)
            elif isinstance(new_item, ToolCallOutputItem):
                response = f"ツール実行結果: {new_item.output}"
                current_responses.append(response)

        # 最後のエージェントの応答をまとめて表示
        if current_responses:
            responses.append({"agent": current_agent_name, "content": "\n\n".join(current_responses)})

        # 応答を表示
        for response in responses:
            with st.chat_message("assistant", avatar=AGENT_ICONS.get(response["agent"], "✨")):
                st.markdown(response["content"])
            st.session_state.messages.append({
                "role": "assistant",
                "agent": response["agent"],
                "content": response["content"]
            })

        # セッションステートを更新
        st.session_state.input_items = result.to_input_list()
        st.session_state.current_agent = result.last_agent
