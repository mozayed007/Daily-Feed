"""
Tests for agent tools
"""

import pytest
from app.tools.fetch_tool import FetchTool
from app.tools.summarize_tool import SummarizeTool
from app.tools.critique_tool import CritiqueTool
from app.tools.deliver_tool import DeliverTool


class TestFetchTool:
    """Tests for FetchTool"""
    
    @pytest.mark.asyncio
    async def test_validate_url_blocks_private_ips(self):
        """Test that private IP ranges are blocked"""
        tool = FetchTool()
        
        # Should block localhost
        assert tool._validate_url("http://localhost/feed") == False
        assert tool._validate_url("http://127.0.0.1/feed") == False
        
        # Should block private ranges
        assert tool._validate_url("http://10.0.0.1/feed") == False
        assert tool._validate_url("http://192.168.1.1/feed") == False
        
        # Should allow valid URLs
        assert tool._validate_url("https://news.ycombinator.com/rss") == True
    
    @pytest.mark.asyncio
    async def test_validate_url_blocks_non_http(self):
        """Test that non-HTTP schemes are blocked"""
        tool = FetchTool()
        
        assert tool._validate_url("ftp://example.com/feed") == False
        assert tool._validate_url("file:///etc/passwd") == False
        assert tool._validate_url("javascript:alert(1)") == False


class TestSummarizeTool:
    """Tests for SummarizeTool"""
    
    @pytest.mark.asyncio
    async def test_parse_response_valid(self):
        """Test parsing valid LLM response"""
        tool = SummarizeTool()
        
        response = """SUMMARY: This is a test summary.

CATEGORY: Technology

SENTIMENT: Positive

KEY POINTS:
- Point 1
- Point 2

READING TIME: 5"""
        
        result = tool._parse_response(response)
        
        assert result["summary"] == "This is a test summary."
        assert result["category"] == "Technology"
        assert result["sentiment"] == "Positive"
        assert len(result["key_points"]) == 2
        assert result["reading_time"] == 5
    
    @pytest.mark.asyncio
    async def test_parse_response_fallback(self):
        """Test parsing with missing fields"""
        tool = SummarizeTool()
        
        response = "Some random text without proper format"
        
        result = tool._parse_response(response)
        
        assert result["summary"] == "Some random text without proper format"  # Full text as fallback
        assert result["category"] == "General"  # Default
        assert result["sentiment"] == "Neutral"  # Default


class TestCritiqueTool:
    """Tests for CritiqueTool"""
    
    @pytest.mark.asyncio
    async def test_parse_critique_valid(self):
        """Test parsing valid critique response"""
        tool = CritiqueTool()
        
        response = """ACCURACY: 8
COMPLETENESS: 7
CLARITY: 9
BIAS: 8
OVERALL SCORE: 8

ISSUES FOUND:
- None

SUGGESTIONS FOR IMPROVEMENT:
Good summary"""
        
        result = tool._parse_critique(response)
        
        assert result["accuracy"] == 8
        assert result["completeness"] == 7
        assert result["overall_score"] == 8
        assert result["passed"] == True  # Assuming default min_score is 7


class TestDeliverTool:
    """Tests for DeliverTool"""
    
    def test_format_digest(self):
        """Test digest formatting"""
        from app.database import ArticleModel
        from datetime import datetime
        
        tool = DeliverTool()
        
        # Create mock articles
        articles = [
            ArticleModel(
                id=1,
                title="Test Article",
                url="https://example.com",
                source="Test Source",
                category="Technology",
                summary="Test summary",
                fetched_at=datetime.utcnow(),
                is_processed=True
            )
        ]
        
        content = tool._format_digest(articles)
        
        assert "DAILY NEWS DIGEST" in content
        assert "Test Article" in content
        assert "Technology" in content
        assert "Test summary" in content
