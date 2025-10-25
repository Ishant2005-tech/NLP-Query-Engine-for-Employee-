from sqlalchemy import inspect, text, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SchemaDiscovery:
    """
    Automatically discover database schema
    Works with any reasonable database structure
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_database(self) -> Dict[str, Any]:
        """
        Discover complete database schema:
        - Tables and their purposes
        - Columns with data types
        - Relationships
        - Sample data for context
        """
        try:
            schema_info = {
                "tables": [],
                "relationships": [],
                "summary": {}
            }
            
            # Detect database type
            db_type = await self._detect_database_type()
            
            # Get all table names
            table_names = await self._get_table_names(db_type)
            
            # Analyze each table
            for table_name in table_names:
                table_info = await self._analyze_table(table_name, db_type)
                schema_info["tables"].append(table_info)
                
            # Discover relationships
            relationships = await self._discover_relationships(db_type)
            schema_info["relationships"] = relationships
            
            # Generate summary
            schema_info["summary"] = {
                "total_tables": len(table_names),
                "total_columns": sum(len(t["columns"]) for t in schema_info["tables"]),
                "total_relationships": len(relationships),
                "database_type": db_type
            }
            
            logger.info(f"Schema discovered: {schema_info['summary']}")
            return schema_info
        
        except Exception as e:
            logger.error(f"Schema discovery error: {e}")
            raise

    async def _detect_database_type(self) -> str:
        """Detect PostgreSQL, MySQL, or SQLite"""
        try:
            result = await self.session.execute(text("SELECT version()"))
            version = result.scalar()
            if "PostgreSQL" in str(version):
                return "postgresql"
            elif "MySQL" in str(version):
                return "mysql"
        except:
            pass
        return "sqlite"

    async def _get_table_names(self, db_type: str) -> List[str]:
        """Get all table names based on database type"""
        if db_type == "postgresql":
            result = await self.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """))
        elif db_type == "sqlite":
            result = await self.session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
            """))
        else: # mysql
            result = await self.session.execute(text("SHOW TABLES"))
        return [row[0] for row in result]

    async def _analyze_table(self, table_name: str, db_type: str) -> Dict[str, Any]:
        """Analyze a single table"""
        # Get column information
        if db_type == "sqlite":
            result = await self.session.execute(
                text(f"PRAGMA table_info({table_name})")
            )
            columns = []
            for row in result:
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "nullable": row[3] == 0,
                    "default": row[4]
                })
        else: # PostgreSQL/MySQL
            result = await self.session.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """), {"table_name": table_name})
            columns = []
            for row in result:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3]
                })
        
        # Get sample data (5 rows)
        try:
            sample_result = await self.session.execute(
                text(f"SELECT * FROM {table_name} LIMIT 5") # Note: table_name is from schema, not user input
            )
            sample_data = [dict(row._mapping) for row in sample_result]
        except:
            sample_data = []
            
        # Infer table purpose
        purpose = self._infer_table_purpose(table_name, columns)
        
        return {
            "name": table_name,
            "purpose": purpose,
            "columns": columns,
            "sample_data": sample_data
        }

    async def _discover_relationships(self, db_type: str) -> List[Dict[str, str]]:
        """Discover foreign key relationships"""
        if db_type == "sqlite":
            # SQLite doesn't have easy FK introspection
            return []
        
        if db_type == "postgresql":
            try:
                result = await self.session.execute(text("""
                    SELECT
                        tc.table_name AS from_table,
                        kcu.column_name AS from_column,
                        ccu.table_name AS to_table,
                        ccu.column_name AS to_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                """))
                relationships = []
                for row in result:
                    relationships.append({
                        "from_table": row[0],
                        "from_column": row[1],
                        "to_table": row[2],
                        "to_column": row[3]
                    })
                return relationships
            except:
                return []
        
        return [] # Default for other DBs like MySQL

    def _infer_table_purpose(self, table_name: str, columns: List[Dict]) -> str:
        """Infer table purpose from name and columns"""
        name_lower = table_name.lower()
        column_names = [c["name"].lower() for c in columns]
        
        # Common patterns
        if any(term in name_lower for term in ["employee", "staff", "personnel", "emp"]):
            return "Employee information"
        elif any(term in name_lower for term in ["department", "dept", "division"]):
            return "Department/organizational structure"
        elif any(term in name_lower for term in ["salary", "compensation", "pay"]):
            return "Salary and compensation data"
        elif any(term in name_lower for term in ["document", "file", "attachment"]):
            return "Document storage"
        else:
            return "General data table"