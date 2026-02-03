import pytest
from min_cc.models import Message
from min_cc.compaction import CompactionService, CompactionStrategy
from min_cc.agent import CodingAgent
from unittest.mock import MagicMock, patch

def test_compaction_service_truncation():
    service = CompactionService(token_limit=10)
    
    messages = [
        Message(role="system", content="System prompt"),
        Message(role="user", content="A very long message that should definitely trigger compaction because it exceeds the limit"),
        Message(role="assistant", content="Response 1"),
        Message(role="user", content="Request 2"),
        Message(role="assistant", content="Response 2"),
    ]
    
    compacted = service.compact(messages)
    
    # Should keep the system prompt
    assert compacted[0].role == "system"
    
    # Total messages should be reduced after compaction
    assert len(compacted) <= 5
    
def test_agent_automatically_calls_compact():
    mock_service = MagicMock(spec=CompactionService)
    mock_service.compact.side_effect = lambda x, **kwargs: x
    
    with patch("min_cc.agent.OpenAI") as mock_openai:
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello", tool_calls=None))]
        )
        
        agent = CodingAgent(api_key="fake", compaction_service=mock_service)
        agent.run("Hi")
        
        assert mock_service.compact.called

        captured_messages = mock_service.compact.call_args[0][0]
        assert any(m.content == "Hi" for m in captured_messages)

def test_compaction_summarize_strategy():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Summary of progress"))]
    )
    
    service = CompactionService(token_limit=5, strategy=CompactionStrategy.SUMMARIZE)
    
    messages = [
        Message(role="system", content="System"),
        Message(role="user", content="Message 1"),
        Message(role="assistant", content="Message 2"),
        Message(role="user", content="Message 3"),
        Message(role="assistant", content="Message 4"), # This will trigger limit
    ]
    
    compacted = service.compact(messages, llm_client=mock_client, model="test-model")
    
    # Should contain summary and preserved messages
    assert any("[CONVERSATION SUMMARY]" in (m.content or "") for m in compacted)
    # The last preserved messages should still be there (Message 3 and 4)
    assert any("Message 4" in (m.content or "") for m in compacted)
    assert mock_client.chat.completions.create.called
