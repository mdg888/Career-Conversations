"""
Comprehensive test suite for app.py
Tests cover initialization, tool calls, chat functionality, evaluation, and error handling
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pydantic import BaseModel
import responses

# Import the modules to test
from src.app import Me, push, record_user_details, record_unknown_question, Evaluation


class TestPushNotifications:
    """Test push notification functionality"""

    @responses.activate
    def test_push_sends_correct_data(self):
        """Test that push function sends correct data to Pushover API"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            push("Test message")

        assert len(responses.calls) == 1
        assert responses.calls[0].request.body
        # Verify the data sent
        assert b"Test message" in responses.calls[0].request.body
        assert b"test_token" in responses.calls[0].request.body
        assert b"test_user" in responses.calls[0].request.body

    @responses.activate
    def test_push_handles_api_failure(self):
        """Test push function behavior when API fails"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            status=500
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            # Should not raise exception
            push("Test message")

    @responses.activate
    def test_record_user_details(self):
        """Test record_user_details function"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            result = record_user_details(
                email="test@example.com",
                name="John Doe",
                notes="Interested in hiring"
            )

        assert result == {"status": "success"}
        assert len(responses.calls) == 1
        assert b"test@example.com" in responses.calls[0].request.body
        assert b"John Doe" in responses.calls[0].request.body

    @responses.activate
    def test_record_user_details_with_defaults(self):
        """Test record_user_details with default parameters"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            result = record_user_details(email="test@example.com")

        assert result == {"status": "success"}
        assert b"Name not provided" in responses.calls[0].request.body

    @responses.activate
    def test_record_unknown_question(self):
        """Test record_unknown_question function"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            result = record_unknown_question("What is the meaning of life?")

        assert result == {"status": "success"}
        assert len(responses.calls) == 1
        assert b"What is the meaning of life?" in responses.calls[0].request.body


class TestMeInitialization:
    """Test Me class initialization"""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Test summary content")
    @patch('src.app.OpenAI')
    def test_me_initialization_success(self, mock_openai, mock_file, mock_pdf):
        """Test successful initialization of Me class"""
        # Mock PDF reading
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn profile text"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()

        assert me.name == "Michael Di Giatnomasso"
        assert me.linkedin == "LinkedIn profile text"
        assert me.summary == "Test summary content"
        mock_openai.assert_called_once()
        mock_pdf.assert_called_once_with("me/profile_summary.pdf")

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_me_initialization_with_multiple_pdf_pages(self, mock_openai, mock_file, mock_pdf):
        """Test initialization with multi-page PDF"""
        # Mock multiple PDF pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf.return_value.pages = [mock_page1, mock_page2]

        me = Me()

        assert me.linkedin == "Page 1 contentPage 2 content"

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_me_initialization_with_empty_pdf_pages(self, mock_openai, mock_file, mock_pdf):
        """Test initialization with PDF pages that return None"""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = None
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Valid content"
        mock_pdf.return_value.pages = [mock_page1, mock_page2]

        me = Me()

        assert me.linkedin == "Valid content"

    @patch('src.app.PdfReader', side_effect=FileNotFoundError("PDF not found"))
    @patch('src.app.OpenAI')
    def test_me_initialization_missing_pdf(self, mock_openai, mock_pdf):
        """Test initialization fails gracefully with missing PDF"""
        with pytest.raises(FileNotFoundError):
            Me()

    @patch('src.app.PdfReader')
    @patch('builtins.open', side_effect=FileNotFoundError("Summary not found"))
    @patch('src.app.OpenAI')
    def test_me_initialization_missing_summary(self, mock_openai, mock_file, mock_pdf):
        """Test initialization fails gracefully with missing summary"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        with pytest.raises(FileNotFoundError):
            Me()


class TestToolCalls:
    """Test tool call handling"""

    @responses.activate
    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_handle_tool_calls_record_user_details(self, mock_openai, mock_file, mock_pdf):
        """Test handle_tool_calls with record_user_details"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            me = Me()

            # Create mock tool call
            mock_tool_call = Mock()
            mock_tool_call.id = "call_123"
            mock_tool_call.function.name = "record_user_details"
            mock_tool_call.function.arguments = json.dumps({
                "email": "test@example.com",
                "name": "John Doe"
            })

            results = me.handle_tool_calls([mock_tool_call])

            assert len(results) == 1
            assert results[0]["role"] == "tool"
            assert results[0]["tool_call_id"] == "call_123"
            assert json.loads(results[0]["content"]) == {"status": "success"}

    @responses.activate
    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_handle_tool_calls_record_unknown_question(self, mock_openai, mock_file, mock_pdf):
        """Test handle_tool_calls with record_unknown_question"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            me = Me()

            mock_tool_call = Mock()
            mock_tool_call.id = "call_456"
            mock_tool_call.function.name = "record_unknown_question"
            mock_tool_call.function.arguments = json.dumps({
                "question": "Unknown question"
            })

            results = me.handle_tool_calls([mock_tool_call])

            assert len(results) == 1
            assert results[0]["tool_call_id"] == "call_456"

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_handle_tool_calls_invalid_tool(self, mock_openai, mock_file, mock_pdf):
        """Test handle_tool_calls with invalid tool name"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()

        mock_tool_call = Mock()
        mock_tool_call.id = "call_789"
        mock_tool_call.function.name = "nonexistent_tool"
        mock_tool_call.function.arguments = json.dumps({})

        results = me.handle_tool_calls([mock_tool_call])

        assert len(results) == 1
        assert json.loads(results[0]["content"]) == {}

    @responses.activate
    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_handle_tool_calls_multiple_calls(self, mock_openai, mock_file, mock_pdf):
        """Test handle_tool_calls with multiple tool calls"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            me = Me()

            mock_tool_call1 = Mock()
            mock_tool_call1.id = "call_1"
            mock_tool_call1.function.name = "record_user_details"
            mock_tool_call1.function.arguments = json.dumps({"email": "test@example.com"})

            mock_tool_call2 = Mock()
            mock_tool_call2.id = "call_2"
            mock_tool_call2.function.name = "record_unknown_question"
            mock_tool_call2.function.arguments = json.dumps({"question": "Test?"})

            results = me.handle_tool_calls([mock_tool_call1, mock_tool_call2])

            assert len(results) == 2
            assert results[0]["tool_call_id"] == "call_1"
            assert results[1]["tool_call_id"] == "call_2"


class TestSystemPrompts:
    """Test system prompt generation"""

    @patch('app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Test summary")
    @patch('app.OpenAI')
    def test_system_prompt_contains_required_elements(self, mock_openai, mock_file, mock_pdf):
        """Test system_prompt contains all required elements"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn profile"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()
        prompt = me.system_prompt()

        assert "Michael Di Giatnomasso" in prompt
        assert "Test summary" in prompt
        assert "LinkedIn profile" in prompt
        assert "record_unknown_question" in prompt
        assert "record_user_details" in prompt

    @patch('app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Test summary")
    @patch('app.OpenAI')
    def test_evaluator_system_prompt_contains_required_elements(self, mock_openai, mock_file, mock_pdf):
        """Test evaluator_system_prompt contains all required elements"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn profile"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()
        prompt = me.evaluator_system_prompt()

        assert "Michael Di Giatnomasso" in prompt
        assert "evaluator" in prompt
        assert "Test summary" in prompt
        assert "LinkedIn profile" in prompt

    @patch('app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Test summary")
    @patch('app.OpenAI')
    def test_evaluator_user_prompt_formatting(self, mock_openai, mock_file, mock_pdf):
        """Test evaluator_user_prompt formats correctly"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()
        history = [{"role": "user", "content": "Hello"}]
        message = "What's your experience?"
        reply = "I have 10 years experience"

        prompt = me.evaluator_user_prompt(reply, message, history)

        assert "Hello" in prompt
        assert "What's your experience?" in prompt
        assert "I have 10 years experience" in prompt


class TestChat:
    """Test chat functionality"""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_chat_without_tool_calls(self, mock_openai_class, mock_file, mock_pdf):
        """Test chat function without tool calls"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        # Setup mock OpenAI client
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock chat response (no tool calls)
        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock()]
        mock_chat_response.choices[0].finish_reason = "stop"
        mock_chat_response.choices[0].message.content = "Hello! How can I help you?"

        mock_openai_instance.chat.completions.create.return_value = mock_chat_response

        # Mock evaluation response
        mock_eval_response = Mock()
        mock_eval_response.choices = [Mock()]
        mock_eval_response.choices[0].message.parsed = Evaluation(
            is_acceptable=True,
            feedback="Good response"
        )
        mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

        me = Me()
        history = []
        reply = me.chat("Hello", history)

        assert reply == "Hello! How can I help you?"
        assert mock_openai_instance.chat.completions.create.call_count == 1

    @responses.activate
    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_chat_with_tool_calls(self, mock_openai_class, mock_file, mock_pdf):
        """Test chat function with tool calls"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            json={"status": 1},
            status=200
        )

        with patch.dict(os.environ, {
            "PUSHOVER_TOKEN": "test_token",
            "PUSHOVER_USER": "test_user"
        }):
            mock_openai_instance = Mock()
            mock_openai_class.return_value = mock_openai_instance

            # First response: tool call
            mock_tool_call = Mock()
            mock_tool_call.id = "call_123"
            mock_tool_call.function.name = "record_user_details"
            mock_tool_call.function.arguments = json.dumps({"email": "test@example.com"})

            mock_first_response = Mock()
            mock_first_response.choices = [Mock()]
            mock_first_response.choices[0].finish_reason = "tool_calls"
            mock_first_response.choices[0].message = Mock()
            mock_first_response.choices[0].message.tool_calls = [mock_tool_call]

            # Second response: final answer
            mock_second_response = Mock()
            mock_second_response.choices = [Mock()]
            mock_second_response.choices[0].finish_reason = "stop"
            mock_second_response.choices[0].message.content = "I've recorded your details!"

            mock_openai_instance.chat.completions.create.side_effect = [
                mock_first_response,
                mock_second_response
            ]

            # Mock evaluation
            mock_eval_response = Mock()
            mock_eval_response.choices = [Mock()]
            mock_eval_response.choices[0].message.parsed = Evaluation(
                is_acceptable=True,
                feedback="Good"
            )
            mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

            me = Me()
            reply = me.chat("My email is test@example.com", [])

            assert reply == "I've recorded your details!"
            assert mock_openai_instance.chat.completions.create.call_count == 2

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_chat_with_evaluation_rejection_and_rerun(self, mock_openai_class, mock_file, mock_pdf):
        """Test chat with evaluation rejection triggering rerun"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        # First chat response
        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock()]
        mock_chat_response.choices[0].finish_reason = "stop"
        mock_chat_response.choices[0].message.content = "Bad response"

        # Rerun response
        mock_rerun_response = Mock()
        mock_rerun_response.choices = [Mock()]
        mock_rerun_response.choices[0].message.content = "Improved response"

        mock_openai_instance.chat.completions.create.side_effect = [
            mock_chat_response,
            mock_rerun_response
        ]

        # Mock evaluation - rejected
        mock_eval_response = Mock()
        mock_eval_response.choices = [Mock()]
        mock_eval_response.choices[0].message.parsed = Evaluation(
            is_acceptable=False,
            feedback="Response not professional enough"
        )
        mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

        me = Me()
        reply = me.chat("Hello", [])

        assert reply == "Improved response"
        # Should call chat completion twice (initial + rerun)
        assert mock_openai_instance.chat.completions.create.call_count == 2

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_chat_openai_api_error(self, mock_openai_class, mock_file, mock_pdf):
        """Test chat handles OpenAI API errors"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        # Simulate API error
        mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")

        me = Me()

        with pytest.raises(Exception) as exc_info:
            me.chat("Hello", [])

        assert "API Error" in str(exc_info.value)


class TestEvaluation:
    """Test evaluation functionality"""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_evaluate_returns_evaluation_object(self, mock_openai_class, mock_file, mock_pdf):
        """Test evaluate returns proper Evaluation object"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        mock_eval_response = Mock()
        mock_eval_response.choices = [Mock()]
        mock_eval_response.choices[0].message.parsed = Evaluation(
            is_acceptable=True,
            feedback="Excellent response"
        )
        mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

        me = Me()
        result = me.evaluate("Good reply", "Question", [])

        assert isinstance(result, Evaluation)
        assert result.is_acceptable is True
        assert result.feedback == "Excellent response"

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_evaluate_with_unacceptable_response(self, mock_openai_class, mock_file, mock_pdf):
        """Test evaluate with unacceptable response"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        mock_eval_response = Mock()
        mock_eval_response.choices = [Mock()]
        mock_eval_response.choices[0].message.parsed = Evaluation(
            is_acceptable=False,
            feedback="Too casual"
        )
        mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

        me = Me()
        result = me.evaluate("Yo what's up", "Hello", [])

        assert result.is_acceptable is False
        assert "Too casual" in result.feedback


class TestRerun:
    """Test rerun functionality"""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_rerun_includes_feedback(self, mock_openai_class, mock_file, mock_pdf):
        """Test rerun includes previous feedback in system prompt"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        mock_rerun_response = Mock()
        mock_rerun_response.choices = [Mock()]
        mock_rerun_response.choices[0].message.content = "Improved answer"
        mock_openai_instance.chat.completions.create.return_value = mock_rerun_response

        me = Me()
        result = me.rerun(
            reply="Bad answer",
            message="What's your experience?",
            history=[],
            feedback="Be more professional"
        )

        assert result == "Improved answer"

        # Verify the system prompt includes feedback
        call_args = mock_openai_instance.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_message = messages[0]['content']

        assert "Bad answer" in system_message
        assert "Be more professional" in system_message
        assert "rejected" in system_message


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('src.app.OpenAI')
    def test_empty_summary_file(self, mock_openai, mock_file, mock_pdf):
        """Test handling of empty summary file"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()
        assert me.summary == ""

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_pdf_with_no_pages(self, mock_openai, mock_file, mock_pdf):
        """Test handling of PDF with no pages"""
        mock_pdf.return_value.pages = []

        me = Me()
        assert me.linkedin == ""

    @responses.activate
    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_handle_tool_calls_with_malformed_json(self, mock_openai, mock_file, mock_pdf):
        """Test handle_tool_calls with malformed JSON arguments"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        me = Me()

        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "record_user_details"
        mock_tool_call.function.arguments = "not valid json"

        with pytest.raises(json.JSONDecodeError):
            me.handle_tool_calls([mock_tool_call])

    @patch('src.app.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data="Summary")
    @patch('src.app.OpenAI')
    def test_chat_with_empty_history(self, mock_openai_class, mock_file, mock_pdf):
        """Test chat with empty history list"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "LinkedIn"
        mock_pdf.return_value.pages = [mock_page]

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        mock_chat_response = Mock()
        mock_chat_response.choices = [Mock()]
        mock_chat_response.choices[0].finish_reason = "stop"
        mock_chat_response.choices[0].message.content = "Reply"
        mock_openai_instance.chat.completions.create.return_value = mock_chat_response

        mock_eval_response = Mock()
        mock_eval_response.choices = [Mock()]
        mock_eval_response.choices[0].message.parsed = Evaluation(
            is_acceptable=True,
            feedback="Good"
        )
        mock_openai_instance.beta.chat.completions.parse.return_value = mock_eval_response

        me = Me()
        reply = me.chat("Hello", [])

        assert reply == "Reply"

    @responses.activate
    def test_push_with_missing_env_vars(self):
        """Test push function with missing environment variables"""
        responses.add(
            responses.POST,
            "https://api.pushover.net/1/messages.json",
            status=200
        )

        with patch.dict(os.environ, {}, clear=True):
            # Should handle gracefully (sends None values)
            push("Test message")
