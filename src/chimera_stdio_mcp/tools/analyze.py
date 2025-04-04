"""Code analysis tool for MCP."""
import os
import re
import structlog
from typing import Any, Dict, List, Optional

from .base import BaseTool

logger = structlog.get_logger(__name__)

class AnalyzeTool(BaseTool):
    """Tool for analyzing code."""
    
    TOOL_NAME = "analyze_code"
    DESCRIPTION = "Analyzes code for common issues and code statistics."
    
    def __init__(self):
        """Initialize the analyze tool."""
        super().__init__()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the analyze_code tool.
        
        Args:
            params: Dictionary containing:
                - code: The code to analyze
                - language: The programming language (optional)
                - file_path: Path to the file (optional)
        
        Returns:
            Dictionary with analysis results
        """
        valid, error = self.validate_params(params, ["code"])
        if not valid:
            return {"error": error}
        
        code = params["code"]
        language = params.get("language")
        file_path = params.get("file_path")
        
        # Determine language if not provided
        if not language and file_path:
            language = self._detect_language_from_path(file_path)
        
        results = {}
        
        # Calculate stats
        results["stats"] = self._calculate_stats(code)
        
        # Find issues
        results["issues"] = self._find_issues(code, language)
        
        return results
    
    def _detect_language_from_path(self, file_path: str) -> Optional[str]:
        """Detect programming language from file path."""
        if not file_path:
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # Map common extensions to languages
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".sh": "bash",
            ".bat": "batch",
            ".ps1": "powershell",
            ".sql": "sql",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".java": "java",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
        }
        
        return ext_map.get(ext)
    
    def _calculate_stats(self, code: str) -> Dict[str, Any]:
        """Calculate code statistics."""
        lines = code.splitlines()
        
        # Count blank lines
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # Count comment lines (simple heuristic)
        comment_lines = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*", "'")))
        
        # Calculate line length statistics
        line_lengths = [len(line) for line in lines if line.strip()]
        avg_line_length = sum(line_lengths) / max(len(line_lengths), 1)
        max_line_length = max(line_lengths) if line_lengths else 0
        
        return {
            "total_lines": len(lines),
            "code_lines": len(lines) - blank_lines - comment_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "avg_line_length": round(avg_line_length, 2),
            "max_line_length": max_line_length,
        }
    
    def _find_issues(self, code: str, language: Optional[str]) -> List[Dict[str, Any]]:
        """Find potential issues in the code."""
        issues = []
        
        # Check for very long lines
        for i, line in enumerate(code.splitlines()):
            if len(line) > 100:
                issues.append({
                    "line": i + 1,
                    "severity": "info",
                    "message": f"Line is {len(line)} characters long (recommended max: 100)"
                })
        
        # Check for TODO/FIXME comments
        todo_pattern = re.compile(r'\b(TODO|FIXME)\b')
        for i, line in enumerate(code.splitlines()):
            match = todo_pattern.search(line)
            if match:
                issues.append({
                    "line": i + 1,
                    "severity": "info",
                    "message": f"Found {match.group(0)} comment"
                })
        
        # Language-specific checks
        if language == "python":
            issues.extend(self._check_python_issues(code))
        elif language in ("javascript", "typescript"):
            issues.extend(self._check_js_issues(code))
        
        return issues
    
    def _check_python_issues(self, code: str) -> List[Dict[str, Any]]:
        """Check for Python-specific issues."""
        issues = []
        
        # Check for bare except
        bare_except_pattern = re.compile(r'\bexcept\s*:')
        for i, line in enumerate(code.splitlines()):
            if bare_except_pattern.search(line):
                issues.append({
                    "line": i + 1,
                    "severity": "warning",
                    "message": "Bare 'except:' should be avoided"
                })
        
        return issues
    
    def _check_js_issues(self, code: str) -> List[Dict[str, Any]]:
        """Check for JavaScript/TypeScript-specific issues."""
        issues = []
        
        # Check for console.log statements
        console_log_pattern = re.compile(r'console\.(log|warn|error|info|debug)')
        for i, line in enumerate(code.splitlines()):
            match = console_log_pattern.search(line)
            if match:
                issues.append({
                    "line": i + 1,
                    "severity": "info",
                    "message": f"Found console.{match.group(1)} statement"
                })
        
        return issues
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the JSON schema for the analyze_code tool."""
        return {
            "name": cls.TOOL_NAME,
            "description": cls.DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to analyze"
                    },
                    "language": {
                        "type": "string",
                        "description": "The programming language of the code"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (used to infer language if not specified)"
                    }
                },
                "required": ["code"]
            }
        } 