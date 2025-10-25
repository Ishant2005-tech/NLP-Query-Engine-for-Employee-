import google.generativeai as genai
from typing import Dict, Any
from ..core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

class TextToSQLConverter:
    """Convert natural language to SQL using Gemini (free tier)"""
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_sql(
        self,
        user_query: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language
        Returns: {sql, explanation, tables_used}
        """
        try:
            # Build prompt
            prompt = self._build_prompt(user_query, schema)
            
            # Generate SQL
            response = self.model.generate_content(prompt)
            sql_text = response.text
            
            # Extract SQL
            sql = self._extract_sql(sql_text)
            
            # Validate
            is_valid, error = self._validate_sql(sql)
            if not is_valid:
                return {
                    "sql": None,
                    "error": error,
                    "explanation": sql_text
                }
                
            # Optimize
            optimized_sql = self._optimize_sql(sql)
            
            return {
                "sql": optimized_sql,
                "explanation": sql_text,
                "tables_used": self._extract_tables(optimized_sql, schema)
            }
        except Exception as e:
            logger.error(f"SQL generation error: {e}")
            return {
                "sql": None,
                "error": str(e)
            }

    def _build_prompt(self, user_query: str, schema: Dict[str, Any]) -> str:
        """Build prompt with schema information"""
        schema_desc = "Database Schema:\n"
        for table in schema["tables"]:
            schema_desc += f"\nTable: {table['name']} ({table['purpose']})\n"
            schema_desc += "Columns:\n"
            for col in table["columns"]:
                schema_desc += f"  {col['name']} ({col['type']})\n"
                
        if schema.get("relationships"):
            schema_desc += "\nRelationships:\n"
            for rel in schema["relationships"]:
                # Correcting a formatting issue from the PDF
                schema_desc += f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}\n"

        prompt = f"""You are a SQL expert. Convert the natural language query to SQL.
{schema_desc}
User Query: {user_query}
Instructions:
1. Generate ONLY the SQL query, no explanations.
2. Use proper JOIN syntax if needed.
3. Add LIMIT 100 to prevent large results.
4. Use correct column and table names from schema.
5. Return SQL between sql and  markers.
SQL Query:
"""
        return prompt

    def _extract_sql(self, text: str) -> str:
        """Extract SQL from LLM response"""
        # Try SQL code block (Correcting PDF typo ``sql)
        match = re.search(r'sql\s*(.+?)', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        # Try SELECT statement
        match = re.search(r'(SELECT.+?;?)', text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            if not sql.endswith(';'):
                sql += ';'
            return sql
            
        return text.strip() # Fallback

    def _validate_sql(self, sql: str) -> tuple[bool, str]:
        """Validate SQL for safety"""
        if not sql:
            return False, "Empty SQL query"
            
        sql_upper = sql.upper()
        
        # Check dangerous operations
        dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'UPDATE']
        for keyword in dangerous:
            if keyword in sql_upper:
                return False, f"Dangerous operation: {keyword}"
                
        # Must start with SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return False, "Query must start with SELECT"
            
        return True, ""

    def _optimize_sql(self, sql: str) -> str:
        """Optimize SQL query"""
        # Add LIMIT if not present
        if 'LIMIT' not in sql.upper():
            sql = sql.rstrip(';') + ' LIMIT 100;'
        return sql

    def _extract_tables(self, sql: str, schema: Dict[str, Any]) -> list:
        """Extract table names used in SQL"""
        tables_used = []
        sql_upper = sql.upper()
        for table in schema["tables"]:
            if table["name"].upper() in sql_upper:
                tables_used.append(table["name"])
        return tables_used