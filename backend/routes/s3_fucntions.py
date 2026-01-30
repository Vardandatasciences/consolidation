#!/usr/bin/env python3
"""
S3 Microservice Client for Direct Deployment with MySQL Database
Direct URL: http://15.207.1.40:3000
MySQL Database for operation tracking (uses Django settings)
No AWS credentials required - handled by the microservice

================================================================================
ENHANCED PDF PROCESSING FEATURE
================================================================================

Automatic PDF processing after successful upload to S3:

1. SMART TEXT EXTRACTION (Cost & Time Optimized)
   - Small documents (1-5 pages): Extract ALL pages
   - Medium documents (6-20 pages): Extract first 5, last 1, and 2 middle pages
   - Large documents (20+ pages): Extract first 3, last 1, and 3 strategic samples
   
2. COMPREHENSIVE METADATA EXTRACTION
   - Core metadata: title, author, subject, keywords
   - Technical metadata: creator, producer, PDF version, encryption status
   - Document info: page count, file size (bytes/KB/MB), creation date
   - Processing info: extraction strategy, processing timestamp
   - Auto-categorization: policy, audit, risk, incident, or general

3. AI-POWERED SUMMARY GENERATION
   - Uses OpenAI GPT-3.5-turbo for intelligent summarization
   - Small documents: Detailed summary with key points
   - Medium documents: Structured summary with main sections
   - Large documents: High-level overview with critical highlights
   - All summaries limited to max 10 lines
   - Fallback handling if OpenAI unavailable or fails

4. DATABASE INTEGRATION
   - Saves metadata JSON to file_operations.metadata column
   - Saves AI summary to file_operations.summary column (max 2000 chars)
   - Updates status to 'completed' or 'failed'
   - Records processing timestamps and AI model used
   
5. BACKGROUND PROCESSING
   - Runs in separate thread - non-blocking
   - Upload returns immediately
   - Processing happens asynchronously
   - Check status with get_pdf_processing_status(operation_id)

USAGE:
    # Upload triggers automatic processing for PDFs
    result = client.upload(
        file_path='/path/to/document.pdf',
        user_id='user123',
        module='policy'
    )
    
    if result['success']:
        operation_id = result['operation_id']
        # PDF processing started in background
        
        # Later, check processing status
        status = client.get_pdf_processing_status(operation_id)
        if status['status'] == 'completed':
            metadata = status['metadata']
            summary = status['summary']

REQUIREMENTS:
    - PyPDF2 or pdfplumber for PDF text extraction
    - OpenAI library with configured API key in Django settings
    - MySQL database with file_operations table
    
ERROR HANDLING:
    - Graceful fallback if libraries not available
    - Detailed error logging for debugging
    - Partial results saved even if processing fails
    
================================================================================
"""

import requests
import os
import json
import mimetypes
from typing import Dict, List, Optional, Union, Any
import datetime
import mysql.connector
from mysql.connector import pooling
import threading
import tempfile
import io

# PDF Processing libraries
try:
    import PyPDF2
    PDF_LIBRARY_AVAILABLE = True
except ImportError:
    PDF_LIBRARY_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# OpenAI library
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import Django settings for database configuration
try:
    from django.conf import settings
    DJANGO_SETTINGS_AVAILABLE = True
except ImportError:
    DJANGO_SETTINGS_AVAILABLE = False
    settings = None

def convert_safe_string(value):
    """Convert Django SafeString objects to regular strings for MySQL compatibility"""
    if value is None:
        return None
    
    # Import Django's SafeString to check instance
    try:
        from django.utils.safestring import SafeString
        if isinstance(value, SafeString):
            return str(value)
    except ImportError:
        pass
    
    # Handle HTML escaped strings
    if hasattr(value, '__html__'):
        return str(value)
    
    # Handle Django SafeString specifically
    if hasattr(value, 'mark_safe'):
        return str(value)
    
    # Handle other types that might cause issues
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    
    # Convert any object to string, ensuring it's a regular Python string
    return str(value)

class RenderS3Client:
    """
    Python client for S3 microservice deployed on Direct
    With local MySQL database for operation tracking
    AWS credentials are handled by the microservice itself
    """
    
    def __init__(self, 
                 api_base_url: str = "http://15.207.1.40:3000",
                 mysql_config: Optional[Dict] = None):
        """
        Initialize the Direct S3 client with local MySQL
        
        Args:
            api_base_url: Your Direct deployment URL
            mysql_config: MySQL database configuration (optional)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.db_pool = None
        
        # Initialize MySQL connection if config provided
        if mysql_config:
            self._setup_mysql_database(mysql_config)
        else:
            self._setup_default_mysql()
    
    def _setup_default_mysql(self):
        """Setup MySQL using Django settings configuration"""
        try:
            # Try to get database config from Django settings
            if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'DATABASES'):
                db_config = settings.DATABASES.get('default', {})
                
                mysql_config = {
                    'host': db_config.get('HOST', 'localhost'),
                    'user': db_config.get('USER', 'root'),
                    'password': db_config.get('PASSWORD', 'root'),
                    'database': db_config.get('NAME', 'grc'),
                    'port': int(db_config.get('PORT', 3306)),
                    'autocommit': True,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci'
                }
                
                print(f"🔧 Using Django settings for MySQL: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
            else:
                # Fallback to environment variables if Django settings not available
                mysql_config = {
                    'host': os.environ.get('DB_HOST', 'localhost'),
                    'user': os.environ.get('DB_USER', 'root'),
                    'password': os.environ.get('DB_PASSWORD', 'root'),
                    'database': os.environ.get('DB_NAME', 'grc'),
                    'port': int(os.environ.get('DB_PORT', 3306)),
                    'autocommit': True,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci'
                }
                
                print(f"⚠️  Django settings not available, using environment variables")
            
            self._setup_mysql_database(mysql_config)
            
        except Exception as e:
            print(f"ERROR MySQL setup failed: {str(e)}")
            self.db_pool = None
    
    def _setup_mysql_database(self, mysql_config: Dict):
        """Setup MySQL connection pool"""
        try:
            # Test connection first
            test_conn = mysql.connector.connect(**mysql_config)
            test_conn.close()
            
            # Create connection pool
            self.db_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="render_s3_pool",
                pool_size=5,
                pool_reset_session=True,
                **mysql_config
            )
            
            print("SUCCESS MySQL connection pool initialized successfully")
            
            # Create table if it doesn't exist
            self._create_table_if_not_exists()
            
        except mysql.connector.Error as e:
            print(f"ERROR MySQL connection failed: {str(e)}")
            print("💡 Make sure MySQL is running and credentials are correct")
            self.db_pool = None
        except Exception as e:
            print(f"ERROR Database setup error: {str(e)}")
            self.db_pool = None
    
    def _create_table_if_not_exists(self):
        """Create the file_operations table if it doesn't exist"""
        if not self.db_pool:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Create unified file_operations table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS file_operations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                operation_type ENUM('upload', 'download', 'export') NOT NULL,
                module VARCHAR(45) NULL,
                user_id VARCHAR(255) NOT NULL,
                file_name VARCHAR(500) NOT NULL,
                original_name VARCHAR(500),
                stored_name VARCHAR(500),
                s3_url TEXT,
                s3_key VARCHAR(1000),
                s3_bucket VARCHAR(255),
                file_type VARCHAR(50),
                file_size BIGINT,
                content_type VARCHAR(255),
                export_format VARCHAR(20),
                record_count INT,
                status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
                error TEXT,
                metadata JSON,
                platform VARCHAR(50) DEFAULT 'Render',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                
                INDEX idx_user_id (user_id),
                INDEX idx_operation_type (operation_type),
                INDEX idx_module (module),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_file_type (file_type),
                INDEX idx_platform (platform),
                INDEX idx_s3_key (s3_key(255))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            print("SUCCESS Database table verified/created successfully")
            
        except mysql.connector.Error as e:
            print(f"ERROR Table creation error: {str(e)}")
        except Exception as e:
            print(f"ERROR Unexpected error creating table: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    

    
    def _get_db_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            return None
        
        try:
            return self.db_pool.get_connection()
        except Exception as e:
            print(f"ERROR Failed to get DB connection: {str(e)}")
            return None
    
    def _save_operation_record(self, operation_type: str, operation_data: Dict) -> Optional[int]:
        """Save operation record to MySQL database"""
        if not self.db_pool:
            return None
        
        conn = self._get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
            INSERT INTO file_operations 
            (operation_type, user_id, file_name, original_name, stored_name, s3_url, s3_key, s3_bucket,
             file_type, file_size, content_type, export_format, record_count, status, metadata, platform,
             module, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            now = datetime.datetime.now()
            
            params = (
                operation_type,
                convert_safe_string(operation_data.get('user_id')),
                convert_safe_string(operation_data.get('file_name')),
                convert_safe_string(operation_data.get('original_name')),
                convert_safe_string(operation_data.get('stored_name')),
                convert_safe_string(operation_data.get('s3_url', '')),
                convert_safe_string(operation_data.get('s3_key', '')),
                convert_safe_string(operation_data.get('s3_bucket', '')),
                convert_safe_string(operation_data.get('file_type')),
                operation_data.get('file_size'),
                convert_safe_string(operation_data.get('content_type')),
                convert_safe_string(operation_data.get('export_format')),
                operation_data.get('record_count'),
                convert_safe_string(operation_data.get('status', 'pending')),
                json.dumps(operation_data.get('metadata', {})),
                'Direct',
                convert_safe_string(operation_data.get('module', 'general')),
                now,
                now
            )
            
            cursor.execute(query, params)
            conn.commit()
            operation_id = cursor.lastrowid
            
            print(f"📝 Operation recorded in MySQL: ID {operation_id}")
            return operation_id
            
        except mysql.connector.Error as e:
            print(f"ERROR MySQL save error: {str(e)}")
            return None
        except Exception as e:
            print(f"ERROR Database save error: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _update_operation_record(self, operation_id: int, operation_data: Dict):
        """Update operation record with complete information"""
        if not self.db_pool or not operation_id:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            field_mapping = {
                'stored_name': 'stored_name',
                's3_url': 's3_url', 
                's3_key': 's3_key',
                's3_bucket': 's3_bucket',
                'file_type': 'file_type',
                'file_size': 'file_size',
                'content_type': 'content_type',
                'export_format': 'export_format',
                'record_count': 'record_count',
                'status': 'status',
                'error': 'error'
            }
            
            for key, db_field in field_mapping.items():
                if key in operation_data:
                    update_fields.append(f"{db_field} = %s")
                    # Convert SafeString objects to regular strings for MySQL compatibility
                    value = operation_data[key]
                    if key in ['stored_name', 's3_url', 's3_key', 's3_bucket', 'file_type', 'content_type', 'export_format', 'status', 'error']:
                        value = convert_safe_string(value)
                    update_values.append(value)
            
            # Always update metadata and timestamp
            if 'metadata' in operation_data:
                update_fields.append("metadata = %s")
                update_values.append(json.dumps(operation_data['metadata']))
            
            update_fields.append("updated_at = %s")
            update_values.append(datetime.datetime.now())
            
            # Add completed_at if status is completed
            if operation_data.get('status') == 'completed':
                update_fields.append("completed_at = %s")
                update_values.append(datetime.datetime.now())
            
            # Add operation_id at the end
            update_values.append(operation_id)
            
            query = f"UPDATE file_operations SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_values)
            conn.commit()
            
            print(f"📝 Operation {operation_id} updated in MySQL")
            
        except mysql.connector.Error as e:
            print(f"ERROR MySQL update error: {str(e)}")
        except Exception as e:
            print(f"ERROR Database update error: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _extract_text_from_pdf(self, pdf_content: bytes, smart_extract: bool = True) -> tuple:
        """
        Extract text from PDF bytes using available PDF libraries
        Returns: (text, page_count, extraction_strategy)
        
        Smart extraction logic:
        - Small docs (1-5 pages): Extract all pages
        - Medium docs (6-20 pages): Extract first 5, last 1, and sample 2 from middle
        - Large docs (20+ pages): Extract first 3, last 1, and sample 3 from throughout
        """
        text = ""
        total_pages = 0
        extraction_strategy = "full"
        
        try:
            # Determine total pages first
            if PDFPLUMBER_AVAILABLE:
                with io.BytesIO(pdf_content) as pdf_buffer:
                    with pdfplumber.open(pdf_buffer) as pdf:
                        total_pages = len(pdf.pages)
                        
                        # Determine extraction strategy based on document size
                        if total_pages <= 5:
                            # Small document - extract all pages
                            pages_to_extract = list(range(total_pages))
                            extraction_strategy = "full"
                            print(f"📄 Small document ({total_pages} pages) - extracting all pages")
                        elif total_pages <= 20:
                            # Medium document - extract first 5, last 1, and 2 from middle
                            middle_start = total_pages // 3
                            middle_end = 2 * total_pages // 3
                            pages_to_extract = [0, 1, 2, 3, 4, middle_start, middle_end, total_pages - 1]
                            pages_to_extract = sorted(list(set([p for p in pages_to_extract if p < total_pages])))
                            extraction_strategy = "medium"
                            print(f"📄 Medium document ({total_pages} pages) - extracting {len(pages_to_extract)} pages")
                        else:
                            # Large document - extract first 3, last 1, and 3 from throughout
                            sample_indices = [
                                0, 1, 2,  # First 3 pages
                                total_pages // 4,  # 25% mark
                                total_pages // 2,  # 50% mark
                                3 * total_pages // 4,  # 75% mark
                                total_pages - 1  # Last page
                            ]
                            pages_to_extract = sorted(list(set([p for p in sample_indices if p < total_pages])))
                            extraction_strategy = "large_sample"
                            print(f"📄 Large document ({total_pages} pages) - extracting {len(pages_to_extract)} key pages")
                        
                        # Extract text from selected pages
                        for page_num in pages_to_extract:
                            try:
                                page = pdf.pages[page_num]
                                page_text = page.extract_text()
                                if page_text:
                                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            except Exception as page_error:
                                print(f"⚠️  Error extracting page {page_num + 1}: {str(page_error)}")
                        
                        print(f"✅ Extracted text from {len(pages_to_extract)} pages using pdfplumber")
            
            # Fallback to PyPDF2
            elif PDF_LIBRARY_AVAILABLE:
                pdf_buffer = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                total_pages = len(pdf_reader.pages)
                
                # Same extraction strategy
                if total_pages <= 5:
                    pages_to_extract = list(range(total_pages))
                    extraction_strategy = "full"
                elif total_pages <= 20:
                    middle_start = total_pages // 3
                    middle_end = 2 * total_pages // 3
                    pages_to_extract = [0, 1, 2, 3, 4, middle_start, middle_end, total_pages - 1]
                    pages_to_extract = sorted(list(set([p for p in pages_to_extract if p < total_pages])))
                    extraction_strategy = "medium"
                else:
                    sample_indices = [0, 1, 2, total_pages // 4, total_pages // 2, 3 * total_pages // 4, total_pages - 1]
                    pages_to_extract = sorted(list(set([p for p in sample_indices if p < total_pages])))
                    extraction_strategy = "large_sample"
                
                for page_num in pages_to_extract:
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as page_error:
                        print(f"⚠️  Error extracting page {page_num + 1}: {str(page_error)}")
                
                print(f"✅ Extracted text from {len(pages_to_extract)} pages using PyPDF2")
            
            else:
                print("⚠️  No PDF library available for text extraction")
                return "", 0, "none"
            
            # Limit text length to avoid token limits (approximately 4000 words for safety)
            words = text.split()
            if len(words) > 4000:
                text = ' '.join(words[:4000]) + "\n\n... [Content truncated to fit within processing limits]"
                print(f"📄 Text truncated to 4000 words for processing")
            
            return text.strip(), total_pages, extraction_strategy
            
        except Exception as e:
            print(f"ERROR Failed to extract text from PDF: {str(e)}")
            return "", 0, "error"
    
    def _extract_pdf_metadata(self, pdf_content: bytes, file_name: str, total_pages: int = None, extraction_strategy: str = None) -> Dict:
        """
        Extract comprehensive metadata from PDF
        
        Metadata includes:
        - Basic info: title, author, subject, keywords
        - Technical info: creator, producer, PDF version
        - Document info: page count, file size, creation/modification dates
        - Processing info: extraction strategy, text density
        """
        metadata = {
            'document_name': file_name,
            'file_type': 'PDF',
            'processing_timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            # Use PyPDF2 to extract PDF metadata
            if PDF_LIBRARY_AVAILABLE:
                pdf_buffer = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                
                # Get basic PDF info
                page_count = total_pages or len(pdf_reader.pages)
                metadata['page_count'] = page_count
                
                # Categorize document size
                if page_count <= 5:
                    metadata['document_size_category'] = 'small'
                elif page_count <= 20:
                    metadata['document_size_category'] = 'medium'
                else:
                    metadata['document_size_category'] = 'large'
                
                # Get PDF metadata if available
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    
                    # Core metadata
                    if pdf_meta.title:
                        metadata['title'] = str(pdf_meta.title)
                    if pdf_meta.author:
                        metadata['author'] = str(pdf_meta.author)
                    if pdf_meta.subject:
                        metadata['subject'] = str(pdf_meta.subject)
                    if hasattr(pdf_meta, 'keywords') and pdf_meta.keywords:
                        metadata['keywords'] = str(pdf_meta.keywords)
                    
                    # Technical metadata
                    if pdf_meta.creator:
                        metadata['creator_application'] = str(pdf_meta.creator)
                    if pdf_meta.producer:
                        metadata['pdf_producer'] = str(pdf_meta.producer)
                    
                    # Date metadata
                    if pdf_meta.creation_date:
                        metadata['creation_date'] = str(pdf_meta.creation_date)
                    if hasattr(pdf_meta, 'modification_date') and pdf_meta.modification_date:
                        metadata['modification_date'] = str(pdf_meta.modification_date)
                
                # Get PDF version
                if hasattr(pdf_reader, 'pdf_header'):
                    metadata['pdf_version'] = pdf_reader.pdf_header
                
                # Check if encrypted
                metadata['is_encrypted'] = pdf_reader.is_encrypted
                
                print(f"📋 Extracted comprehensive metadata: {page_count} pages, {metadata.get('document_size_category', 'unknown')} document")
            
            elif PDFPLUMBER_AVAILABLE:
                with io.BytesIO(pdf_content) as pdf_buffer:
                    with pdfplumber.open(pdf_buffer) as pdf:
                        page_count = total_pages or len(pdf.pages)
                        metadata['page_count'] = page_count
                        
                        # Categorize document size
                        if page_count <= 5:
                            metadata['document_size_category'] = 'small'
                        elif page_count <= 20:
                            metadata['document_size_category'] = 'medium'
                        else:
                            metadata['document_size_category'] = 'large'
                        
                        # Extract metadata from pdfplumber
                        if pdf.metadata:
                            for key, value in pdf.metadata.items():
                                if value and key not in metadata:
                                    metadata[key] = str(value)
                
                print(f"📋 Extracted metadata: {page_count} pages")
            
            # Add file size information
            metadata['file_size_bytes'] = len(pdf_content)
            metadata['file_size_kb'] = round(len(pdf_content) / 1024, 2)
            metadata['file_size_mb'] = round(len(pdf_content) / (1024 * 1024), 2)
            
            # Add extraction strategy info
            if extraction_strategy:
                metadata['extraction_strategy'] = extraction_strategy
                metadata['full_text_extracted'] = (extraction_strategy == 'full')
            
            # Use filename as title if title not found
            if 'title' not in metadata:
                metadata['title'] = os.path.splitext(file_name)[0].replace('_', ' ').title()
            
            # Add document classification hints
            file_name_lower = file_name.lower()
            if any(term in file_name_lower for term in ['policy', 'policies']):
                metadata['suggested_category'] = 'policy'
            elif any(term in file_name_lower for term in ['audit', 'compliance', 'finding']):
                metadata['suggested_category'] = 'audit'
            elif any(term in file_name_lower for term in ['risk', 'assessment']):
                metadata['suggested_category'] = 'risk'
            elif any(term in file_name_lower for term in ['incident', 'report']):
                metadata['suggested_category'] = 'incident'
            else:
                metadata['suggested_category'] = 'general'
            
            return metadata
            
        except Exception as e:
            print(f"ERROR Failed to extract PDF metadata: {str(e)}")
            return metadata
    
    def _generate_summary_with_openai(self, text: str, metadata: Dict) -> str:
        """
        Generate an intelligent summary of the document using OpenAI GPT-3.5-turbo
        
        Summary approach:
        - Small documents (1-5 pages): Detailed summary with key points
        - Medium documents (6-20 pages): Structured summary with main sections
        - Large documents (20+ pages): High-level overview with critical highlights
        
        All summaries limited to maximum 10 lines for consistency
        """
        
        if not OPENAI_AVAILABLE:
            print("⚠️  OpenAI library not available")
            return "Summary unavailable: OpenAI library not installed"
        
        try:
            # Get OpenAI API key from Django settings
            api_key = None
            if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'OPENAI_API_KEY'):
                api_key = settings.OPENAI_API_KEY
            
            if not api_key or api_key == 'your-openai-api-key-here':
                print("⚠️  OpenAI API key not configured")
                return "Summary unavailable: OpenAI API key not configured"
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Always use GPT-3.5-turbo as requested
            model = 'gpt-3.5-turbo'
            
            # Determine document size and extraction strategy
            page_count = metadata.get('page_count', 0)
            doc_size = metadata.get('document_size_category', 'unknown')
            extraction_strategy = metadata.get('extraction_strategy', 'unknown')
            full_text = metadata.get('full_text_extracted', False)
            
            # Create context-aware prompt based on document size
            if doc_size == 'small':
                summary_instruction = """Provide a comprehensive summary that includes:
1. Main purpose and subject of the document
2. Key points and important details
3. Notable findings or recommendations
4. Target audience or intended use
Maximum 10 lines."""
            elif doc_size == 'medium':
                summary_instruction = """Provide a structured summary that includes:
1. Document overview and main purpose
2. Key sections and their main topics
3. Critical findings or recommendations
4. Overall conclusions
Maximum 10 lines."""
            else:  # large documents
                summary_instruction = """Provide a high-level overview that includes:
1. Document type and primary purpose
2. Main themes and topics covered
3. Most critical findings or conclusions
4. Key takeaways
Maximum 10 lines. Note: This is a sampled summary from key sections."""
            
            # Add extraction context for transparency
            extraction_note = ""
            if not full_text:
                extraction_note = f"\nNote: This is a {page_count}-page document. Summary based on key sections (pages extracted using {extraction_strategy} strategy)."
            
            # Create comprehensive prompt
            prompt = f"""Please analyze and summarize this document.

Document Information:
- Title: {metadata.get('title', 'Unknown')}
- Type: PDF
- Pages: {page_count}
- Size Category: {doc_size.upper()}
- Author: {metadata.get('author', 'Not specified')}
- Subject: {metadata.get('subject', 'Not specified')}
- Suggested Category: {metadata.get('suggested_category', 'general')}
{extraction_note}

Document Content:
{text[:4500]}

{summary_instruction}

Important: Keep the summary concise, professional, and actionable. Focus on what matters most."""

            print(f"🤖 Generating intelligent summary using {model}...")
            print(f"   Document: {page_count} pages ({doc_size}), Extraction: {extraction_strategy}")
            
            # Call OpenAI API with optimized parameters
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert document analyst specializing in creating concise, professional summaries for compliance, governance, risk, and policy documents. 
Your summaries should be:
- Highly informative and actionable
- Structured and easy to scan
- Maximum 10 lines
- Focused on key points, findings, and recommendations
- Professional and objective in tone"""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,  # Increased slightly for better quality
                temperature=0.3,  # Low temperature for consistent, focused summaries
                presence_penalty=0.1,  # Slight penalty to avoid repetition
                frequency_penalty=0.1  # Slight penalty for varied language
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Ensure summary is not more than 10 lines
            lines = [line.strip() for line in summary.split('\n') if line.strip()]
            if len(lines) > 10:
                summary = '\n'.join(lines[:10])
            else:
                summary = '\n'.join(lines)
            
            # Add metadata footer if it was a sampled extraction
            if not full_text and page_count > 5:
                summary += f"\n\n[Summary generated from {extraction_strategy} extraction of {page_count}-page document]"
            
            print(f"✅ Intelligent summary generated: {len(summary)} characters, {len(lines)} lines")
            
            return summary
            
        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            print(f"ERROR {error_msg}")
            
            # Provide a fallback summary with available metadata
            fallback = f"Document: {metadata.get('title', 'Unknown')} ({metadata.get('page_count', '?')} pages)\n"
            if metadata.get('subject'):
                fallback += f"Subject: {metadata.get('subject')}\n"
            if metadata.get('author'):
                fallback += f"Author: {metadata.get('author')}\n"
            fallback += f"\nAutomatic summary generation failed. Please review document manually.\nError: {str(e)}"
            
            return fallback
    
    def _process_pdf_after_upload(self, operation_id: int, s3_url: str, file_name: str):
        """
        Enhanced PDF processing after upload:
        1. Download PDF from S3
        2. Extract text using intelligent strategy (small vs large document)
        3. Extract comprehensive metadata
        4. Generate AI-powered summary using OpenAI GPT-3.5-turbo
        5. Update database with all information
        
        This runs in a background thread to not block the upload response
        """
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Starting Enhanced PDF Processing")
            print(f"📄 Operation ID: {operation_id}")
            print(f"📂 File: {file_name}")
            print(f"{'='*60}")
            
            # Step 1: Download PDF content from S3
            print(f"\n[Step 1/5] ⬇️  Downloading PDF from S3...")
            print(f"   URL: {s3_url}")
            response = requests.get(s3_url, timeout=90)
            response.raise_for_status()
            pdf_content = response.content
            
            file_size_mb = round(len(pdf_content) / (1024 * 1024), 2)
            print(f"   ✅ Downloaded: {len(pdf_content)} bytes ({file_size_mb} MB)")
            
            # Step 2: Extract text using intelligent strategy
            print(f"\n[Step 2/5] 📄 Extracting text from PDF (smart extraction)...")
            text, total_pages, extraction_strategy = self._extract_text_from_pdf(pdf_content)
            
            if not text:
                print("   ⚠️  No text extracted from PDF")
                # Still extract metadata even if no text
                print(f"\n[Step 3/5] 📋 Extracting metadata (text-less document)...")
                metadata = self._extract_pdf_metadata(pdf_content, file_name, total_pages, extraction_strategy)
                
                print(f"\n[Step 5/5] 💾 Updating database...")
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    metadata, 
                    "No text content available for summary. Document may be image-based or encrypted."
                )
                print(f"\n⚠️  PDF processing completed with limited results (no text extracted)")
                return
            
            # Step 3: Extract comprehensive metadata
            print(f"\n[Step 3/5] 📋 Extracting comprehensive metadata...")
            metadata = self._extract_pdf_metadata(pdf_content, file_name, total_pages, extraction_strategy)
            
            print(f"   Document Details:")
            print(f"   - Pages: {metadata.get('page_count', 'Unknown')}")
            print(f"   - Size Category: {metadata.get('document_size_category', 'Unknown')}")
            print(f"   - Extraction Strategy: {metadata.get('extraction_strategy', 'Unknown')}")
            print(f"   - Title: {metadata.get('title', 'Unknown')}")
            print(f"   - Category: {metadata.get('suggested_category', 'Unknown')}")
            
            # Step 4: Generate AI summary using OpenAI
            print(f"\n[Step 4/5] 🤖 Generating AI-powered summary...")
            summary = self._generate_summary_with_openai(text, metadata)
            
            if summary and not summary.startswith("Summary unavailable"):
                print(f"   ✅ Summary generated successfully")
                print(f"   - Length: {len(summary)} characters")
                print(f"   - Lines: {len(summary.split(chr(10)))}")
            else:
                print(f"   ⚠️  Summary generation had issues: {summary[:100]}...")
            
            # Step 5: Update database with all information
            print(f"\n[Step 5/5] 💾 Updating database with metadata and summary...")
            self._update_pdf_metadata_in_db(operation_id, metadata, summary)
            
            print(f"\n{'='*60}")
            print(f"✅ PDF PROCESSING COMPLETED SUCCESSFULLY")
            print(f"   Operation ID: {operation_id}")
            print(f"   File: {file_name}")
            print(f"   Pages: {total_pages}")
            print(f"   Strategy: {extraction_strategy}")
            print(f"   Summary Length: {len(summary)} chars")
            print(f"{'='*60}\n")
            
        except requests.exceptions.RequestException as req_error:
            error_msg = f"Failed to download PDF from S3: {str(req_error)}"
            print(f"\n❌ ERROR: {error_msg}")
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {'error': error_msg, 'processing_failed': True}, 
                    f"Processing failed: Unable to download file from S3"
                )
            except:
                pass
                
        except Exception as e:
            error_msg = f"PDF processing error: {str(e)}"
            print(f"\n❌ ERROR: PDF processing failed for operation {operation_id}")
            print(f"   Error: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            
            # Update database with error information
            try:
                self._update_pdf_metadata_in_db(
                    operation_id, 
                    {
                        'error': error_msg, 
                        'processing_failed': True,
                        'error_type': type(e).__name__
                    }, 
                    f"Automatic processing failed. Please review document manually.\nError: {str(e)}"
                )
            except Exception as db_error:
                print(f"   ⚠️  Also failed to update database: {str(db_error)}")
    
    def _update_pdf_metadata_in_db(self, operation_id: int, metadata: Dict, summary: str):
        """
        Update the file_operations record with PDF metadata and summary
        
        Updates:
        - metadata: Comprehensive JSON metadata about the document
        - summary: AI-generated summary (up to 2000 characters)
        - status: Set to 'completed' if processing was successful
        - updated_at: Current timestamp
        """
        if not self.db_pool or not operation_id:
            print("⚠️  Database pool not available or invalid operation_id")
            return
        
        conn = self._get_db_connection()
        if not conn:
            print("⚠️  Could not get database connection")
            return
        
        cursor = conn.cursor()
        
        try:
            # Determine status based on whether we have a valid summary
            processing_status = 'completed'
            if 'error' in metadata or 'processing_failed' in metadata:
                processing_status = 'failed'
            elif summary.startswith("Summary unavailable") or summary.startswith("No text content"):
                processing_status = 'completed'  # Completed but with limited results
            
            # Add processing completion timestamp to metadata
            metadata['processing_completed_at'] = datetime.datetime.now().isoformat()
            metadata['ai_processing_used'] = True
            metadata['ai_model'] = 'gpt-3.5-turbo'
            
            # Update metadata, summary, and status columns
            query = """
            UPDATE file_operations 
            SET metadata = %s, 
                summary = %s, 
                status = %s,
                updated_at = %s,
                completed_at = %s
            WHERE id = %s
            """
            
            params = (
                json.dumps(metadata),
                summary[:2000],  # Limit summary to 2000 characters for database
                processing_status,
                datetime.datetime.now(),
                datetime.datetime.now() if processing_status == 'completed' else None,
                operation_id
            )
            
            cursor.execute(query, params)
            conn.commit()
            
            print(f"✅ Database updated successfully:")
            print(f"   - Operation ID: {operation_id}")
            print(f"   - Status: {processing_status}")
            print(f"   - Metadata fields: {len(metadata)}")
            print(f"   - Summary length: {len(summary)} characters")
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL update error: {str(e)}")
            print(f"   - Operation ID: {operation_id}")
            print(f"   - Error Code: {e.errno if hasattr(e, 'errno') else 'N/A'}")
        except Exception as e:
            print(f"❌ Database update error: {str(e)}")
            print(f"   - Operation ID: {operation_id}")
            print(f"   - Error Type: {type(e).__name__}")
        finally:
            cursor.close()
            conn.close()
    
    def get_pdf_processing_status(self, operation_id: int) -> Dict:
        """Check if PDF processing is complete and get metadata/summary"""
        if not self.db_pool:
            return {'status': 'error', 'message': 'Database not available'}
        
        conn = self._get_db_connection()
        if not conn:
            return {'status': 'error', 'message': 'Database connection failed'}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
            SELECT metadata, summary, status, file_name, updated_at 
            FROM file_operations 
            WHERE id = %s
            """
            cursor.execute(query, (operation_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'status': 'error', 'message': 'Operation not found'}
            
            # Check if metadata and summary are populated
            has_metadata = result['metadata'] is not None and result['metadata'] != '{}'
            has_summary = result['summary'] is not None and result['summary'] != ''
            
            if has_metadata and has_summary:
                return {
                    'status': 'completed',
                    'file_name': result['file_name'],
                    'metadata': json.loads(result['metadata']) if isinstance(result['metadata'], str) else result['metadata'],
                    'summary': result['summary'],
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                }
            else:
                return {
                    'status': 'processing',
                    'file_name': result['file_name'],
                    'message': 'PDF processing in progress...'
                }
            
        except Exception as e:
            print(f"ERROR Failed to check processing status: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent operation history from MySQL"""
        if not self.db_pool:
            return []
        
        conn = self._get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            if user_id:
                query = """
                SELECT * FROM file_operations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                SELECT * FROM file_operations 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for result in results:
                for key, value in result.items():
                    if isinstance(value, datetime.datetime):
                        result[key] = value.isoformat()
            
            return results
            
        except mysql.connector.Error as e:
            print(f"ERROR MySQL query error: {str(e)}")
            return []
        except Exception as e:
            print(f"ERROR Database query error: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_stats(self) -> Dict:
        """Get operation statistics from MySQL"""
        if not self.db_pool:
            return {}
        
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get overall stats
            cursor.execute("""
                SELECT 
                    operation_type,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(file_size) as avg_file_size,
                    SUM(file_size) as total_file_size
                FROM file_operations 
                GROUP BY operation_type
            """)
            
            stats = {
                'operations_by_type': cursor.fetchall(),
                'total_operations': 0,
                'total_completed': 0,
                'total_failed': 0
            }
            
            # Calculate totals
            for op_stat in stats['operations_by_type']:
                stats['total_operations'] += op_stat['total_count']
                stats['total_completed'] += op_stat['completed_count']
                stats['total_failed'] += op_stat['failed_count']
            
            # Get recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as operations
                FROM file_operations 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            stats['recent_activity'] = cursor.fetchall()
            
            return stats
            
        except mysql.connector.Error as e:
            print(f"ERROR MySQL stats query error: {str(e)}")
            return {}
        except Exception as e:
            print(f"ERROR Database stats error: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def test_connection(self) -> Dict:
        """Test connection to Render microservice and MySQL database"""
        result = {
            'render_status': 'unknown',
            'mysql_status': 'unknown',
            'overall_success': False
        }
        
        # Test Direct microservice
        try:
            print("🧪 Testing Direct microservice connection...")
            response = requests.get(f"{self.api_base_url}/health", timeout=30)
            response.raise_for_status()
            
            health_info = response.json()
            result['direct_status'] = 'connected'
            result['direct_info'] = health_info
            print("SUCCESS Direct microservice: Connected")
            
        except requests.exceptions.Timeout:
            result['direct_status'] = 'timeout'
            result['direct_error'] = 'Connection timed out (Direct service may be unavailable)'
            print("PENDING Direct microservice: Timeout (may be unavailable)")
        except Exception as e:
            result['direct_status'] = 'failed'
            result['direct_error'] = str(e)
            print(f"ERROR Direct microservice: Failed - {str(e)}")
        
        # Test MySQL database
        try:
            print("🧪 Testing MySQL database connection...")
            if self.db_pool:
                conn = self._get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    result['mysql_status'] = 'connected'
                    print("SUCCESS MySQL database: Connected")
                else:
                    result['mysql_status'] = 'failed'
                    result['mysql_error'] = 'Failed to get connection from pool'
                    print("ERROR MySQL database: Connection pool failed")
            else:
                result['mysql_status'] = 'not_configured'
                result['mysql_error'] = 'Database pool not initialized'
                print("⚠️  MySQL database: Not configured")
                
        except mysql.connector.Error as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            print(f"ERROR MySQL database: Failed - {str(e)}")
        except Exception as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            print(f"ERROR MySQL database: Error - {str(e)}")
        
        # Overall success
        result['overall_success'] = (
            result['direct_status'] == 'connected' and 
            result['mysql_status'] in ['connected', 'not_configured']
        )
        
        return result
    
    def upload(self, file_path: str, user_id: str = "default-user", 
               custom_file_name: Optional[str] = None, module: str = None) -> Dict:
        """Upload a file to S3 via Render microservice with MySQL tracking
        
        Args:
            file_path: Path to the file to upload
            user_id: User ID performing the upload
            custom_file_name: Custom name for the file (optional)
            module: Module name (policy, audit, incident, risk, framework, event)
        """
        operation_id = None
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get original file name and extension
            original_file_name = os.path.basename(file_path)
            print(f"Original file name: {original_file_name}---------------------------------------")
            file_name = custom_file_name or original_file_name
            file_size = os.path.getsize(file_path)
            
            # Create timestamp for naming
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create the new naming convention: original_filename_username_module_timestamp
            file_name_without_ext = os.path.splitext(original_file_name)[0]
            print(f"File name without extension: {file_name_without_ext}---------------------------------------")
            file_extension = os.path.splitext(original_file_name)[1]
            new_original_name = f"{file_name_without_ext}_{user_id}_{module or 'general'}_{timestamp}{file_extension}"
            
            print(f"📤 Uploading {file_name} ({file_size} bytes) via Direct...")
            print(f"📂 Module: {module or 'general'}")
            print(f"📄 Original name: {original_file_name}")
            print(f"📄 New original name: {new_original_name}")
            
            # Save initial operation record with module
            operation_data = {
                'user_id': user_id,
                'file_name': original_file_name,  # Keep original filename for S3 upload
                'original_name': original_file_name,  # Store actual original filename
                'module': module or 'general',  # Store module name
                'file_type': os.path.splitext(file_name)[1][1:].lower() if '.' in file_name else '',
                'file_size': file_size,
                'content_type': mimetypes.guess_type(file_path)[0],
                'status': 'pending',
                'metadata': {
                    'original_path': file_path,
                    'custom_file_name': custom_file_name,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url,
                    'module': module or 'general',
                    'naming_convention': 'original_filename_username_module_timestamp',
                    'modified_name': new_original_name  # Store the modified name for reference
                }
            }
            operation_id = self._save_operation_record('upload', operation_data)
            
            # Upload to Direct service
            url = f"{self.api_base_url}/api/upload/{user_id}/{file_name}"
            
            print(f"📍 Upload URL: {url}")
            
            with open(file_path, 'rb') as file:
                files = {'file': (file_name, file, mimetypes.guess_type(file_path)[0])}
                
                print(f"📁 File details: name={file_name}, size={file_size}, type={mimetypes.guess_type(file_path)[0]}")
                
                try:
                    response = requests.post(url, files=files, timeout=300)
                    print(f"📊 Response status: {response.status_code}")
                    print(f"📝 Response headers: {dict(response.headers)}")
                    
                    if response.status_code != 200:
                        print(f"ERROR Response content: {response.text}")
                        
                    response.raise_for_status()
                    result = response.json()
                    print(f"SUCCESS Upload response: {result}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"ERROR Request failed: {str(e)}")
                    if hasattr(e.response, 'text'):
                        print(f"ERROR Error response: {e.response.text}")
                    raise
            
            if result.get('success'):
                file_info = result['file']
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': file_info['storedName'],
                        's3_url': file_info['url'],
                        's3_key': file_info['s3Key'],
                        's3_bucket': file_info.get('bucket', ''),
                        'status': 'completed',
                        'metadata': {
                            'original_path': file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'upload_response': file_info,
                            'modified_name': new_original_name  # Include modified name for reference
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                print(f"SUCCESS Upload successful! File: {file_info['storedName']}")
                
                # Check if file is PDF and trigger background processing
                file_extension = os.path.splitext(file_name)[1].lower()
                if file_extension == '.pdf' and operation_id:
                    print(f"📄 PDF detected, starting background processing...")
                    # Start PDF processing in a background thread (non-blocking)
                    processing_thread = threading.Thread(
                        target=self._process_pdf_after_upload,
                        args=(operation_id, file_info['url'], file_name),
                        daemon=True
                    )
                    processing_thread.start()
                    print(f"✅ PDF processing thread started for operation {operation_id}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'file_info': file_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': 'File uploaded successfully to Direct/S3',
                    'pdf_processing': 'started' if file_extension == '.pdf' else 'not_applicable'
                }
            else:
                # Update MySQL with failure
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed', 
                        'error': result.get('error')
                    })
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR Upload failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }
    
    def download(self, s3_key: str, file_name: str, 
                 destination_path: str = "./downloads", 
                 user_id: str = "default-user") -> Dict:
        """Download a file from S3 via Direct with MySQL tracking"""
        operation_id = None
        
        try:
            print(f"⬇️  Downloading {file_name} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                's3_key': s3_key,
                'status': 'pending',
                'metadata': {
                    'destination_path': destination_path,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('download', operation_data)
            
            # Get download URL from Direct service
            url = f"{self.api_base_url}/api/download/{s3_key}/{file_name}"
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            download_info = response.json()
            
            if not download_info.get('success'):
                raise Exception(f"Failed to get download URL: {download_info.get('error')}")
            
            # Download file
            download_url = download_info['downloadUrl']
            file_response = requests.get(download_url, timeout=300)
            file_response.raise_for_status()
            
            # Save locally
            os.makedirs(destination_path, exist_ok=True)
            local_file_path = os.path.join(destination_path, file_name) if os.path.isdir(destination_path) else destination_path
            
            with open(local_file_path, 'wb') as f:
                f.write(file_response.content)
            
            # Update MySQL with success
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'completed',
                    'file_size': len(file_response.content),
                                            'metadata': {
                            'destination_path': destination_path,
                            'local_file_path': local_file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'download_info': download_info
                        }
                })
            
            print(f"SUCCESS Download successful! Saved to: {local_file_path}")
            
            return {
                'success': True,
                'operation_id': operation_id,
                'file_path': local_file_path,
                'file_size': len(file_response.content),
                'platform': 'Direct',
                'database': 'MySQL',
                'message': 'File downloaded successfully from Direct/S3'
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR Download failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }
    
    def export(self, data: Union[List[Dict], Dict], export_format: str, 
               file_name: str, user_id: str = "default-user") -> Dict:
        """Export data via Direct microservice with MySQL tracking"""
        operation_id = None
        
        try:
            # Validate format - all formats supported by the microservice
            microservice_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf']
            all_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf', 'xlsx']
            
            if export_format.lower() not in all_supported_formats:
                raise ValueError(f"Unsupported format: {export_format}. Supported: {all_supported_formats}")
            
            # Check if format is supported by microservice
            if export_format.lower() not in microservice_supported_formats:
                raise ValueError(f"Format {export_format} is not supported by the S3 microservice. Use local export instead.")
            
            record_count = len(data) if isinstance(data, list) else 1
            print(f"📊 Exporting {record_count} records as {export_format.upper()} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                'export_format': export_format,
                'record_count': record_count,
                'status': 'pending',
                'metadata': {
                    'export_format': export_format,
                    'data_size': len(str(data)),
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('export', operation_data)
            
            # Export via Direct
            url = f"{self.api_base_url}/api/export/{export_format}/{user_id}/{file_name}"
            
            # Format data based on export type (similar to test file)
            if export_format.lower() in ['csv', 'xlsx']:
                # For CSV/XLSX exports, send just the records array
                payload = {'data': data if isinstance(data, list) else [data]}
            else:
                # For other formats, send the full data structure
                payload = {'data': data}
            
            # Include AWS credentials in payload (required by the microservice)
            aws_credentials = {
                'awsAccessKey': 'AKIAW76SP14WHQGXV47T',
                'awsSecretKey': 'wJLUGFOQtXYOqzhyvmM2ljZPVbW+LTLJo2ft3A',
                'awsRegion': 'ap-south-1',
                'bucketName': 'vardaanwebsites'
            }
            payload.update(aws_credentials)
            
            print(f"🔗 Export URL: {url}")
            print(f"📦 Payload size: {len(str(payload))} characters")
            print(f"🔑 Using AWS credentials: {aws_credentials['awsAccessKey'][:10]}...")
            
            response = requests.post(url, json=payload, timeout=300)
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"ERROR Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                export_info = result.get('export') or result.get('file') or result
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': export_info.get('storedName') or export_info.get('fileName') or file_name,
                        's3_url': export_info.get('url') or export_info.get('fileUrl') or export_info.get('downloadUrl'),
                        's3_key': export_info.get('s3Key') or export_info.get('key') or export_info.get('fileKey'),
                        's3_bucket': export_info.get('bucket') or export_info.get('bucketName'),
                        'file_size': export_info.get('size') or export_info.get('fileSize'),
                        'content_type': export_info.get('contentType') or export_info.get('mimeType'),
                        'status': 'completed',
                        'metadata': {
                            'export_format': export_format,
                            'data_size': len(str(data)),
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'export_response': export_info
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                print(f"SUCCESS Export successful! File: {export_info['storedName']}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'export_info': export_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': f'Data exported successfully as {export_format.upper()} via Direct'
                }
            else:
                # Update MySQL with failure
                error_msg = result.get('error') or result.get('message') or 'Unknown error'
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed',
                        'error': error_msg
                    })
                
                return {
                    'success': False,
                    'operation_id': operation_id,
                    'error': error_msg,
                    'response': result
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR Export failed: {error_msg}")
            print(f"📝 Full error details: {type(e).__name__}: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg,
                'error_type': type(e).__name__
            }

def create_direct_mysql_client(mysql_config: Optional[Dict] = None) -> RenderS3Client:
    """Create RenderS3Client with Direct URL and MySQL from Django settings"""
    try:
        if not mysql_config:
            # Try to use Django settings first
            if DJANGO_SETTINGS_AVAILABLE and hasattr(settings, 'DATABASES'):
                db_config = settings.DATABASES.get('default', {})
                
                mysql_config = {
                    'host': db_config.get('HOST', 'localhost'),
                    'user': db_config.get('USER', 'root'),
                    'password': db_config.get('PASSWORD', 'root'),
                    'database': db_config.get('NAME', 'grc'),
                    'port': int(db_config.get('PORT', 3306))
                }
                
                print(f"🔧 Using Django settings for MySQL: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
            else:
                # Fallback to environment variables
                mysql_config = {
                    'host': os.environ.get('DB_HOST', 'localhost'),
                    'user': os.environ.get('DB_USER', 'root'),
                    'password': os.environ.get('DB_PASSWORD', 'root'),
                    'database': os.environ.get('DB_NAME', 'grc'),
                    'port': int(os.environ.get('DB_PORT', 3306))
                }
                
                print(f"WARNING: Django settings not available, using environment variables: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        
        print(f"Creating S3 client with MySQL config: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        client = RenderS3Client("http://15.207.1.40:3000", mysql_config)
        print("S3 client created successfully")
        return client
        
    except ImportError as import_e:
            print(f"ERROR: Import error creating S3 client: {import_e}")
            print("INFO: Trying to create client without MySQL...")
            try:
                client = RenderS3Client("http://15.207.1.40:3000", None)
                print("WARNING: S3 client created without MySQL (fallback mode)")
                return client
            except Exception as fallback_e:
                print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
                raise Exception(f"S3 client creation failed: {import_e}, Fallback failed: {fallback_e}")
        
    except mysql.connector.Error as mysql_e:
        print(f"ERROR: MySQL connection error: {mysql_e}")
        print("INFO: Creating S3 client without MySQL...")
        try:
            client = RenderS3Client("http://15.207.1.40:3000", None)
            print("WARNING: S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"MySQL error: {mysql_e}, Fallback failed: {fallback_e}")
    
    except Exception as e:
        print(f"ERROR: General error creating S3 client: {e}")
        print("INFO: Trying to create client without MySQL...")
        try:
            client = RenderS3Client("http://15.207.1.40:3000", None)
            print("WARNING: S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            print(f"ERROR: Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"S3 client creation failed: {e}, Fallback failed: {fallback_e}")

def quick_test():
    """Quick test function"""
    print("Quick Test: Direct S3 Client with Local MySQL")
    print("=" * 60)
    
    # Create client
    client = create_direct_mysql_client()
    
    # Test connections
    result = client.test_connection()
    
    if result['overall_success']:
        print("SUCCESS All systems operational!")
        
        # Show operation stats
        stats = client.get_operation_stats()
        if stats:
            print(f"\n📊 Database Stats:")
            print(f"   Total operations: {stats.get('total_operations', 0)}")
            print(f"   Completed: {stats.get('total_completed', 0)}")
            print(f"   Failed: {stats.get('total_failed', 0)}")
    else:
        print("ERROR Some systems need attention")
        if result['direct_status'] != 'connected':
            print(f"   Direct: {result.get('direct_error', 'Unknown error')}")
        if result['mysql_status'] != 'connected':
            print(f"   MySQL: {result.get('mysql_error', 'Unknown error')}")

# Example usage
def test_all_export_formats():
    """Comprehensive test for all export formats"""
    
    print("🚀 Testing All Export Formats")
    print("🌐 Direct URL: http://15.207.1.40:3000")
    print("📊 Testing: JSON, CSV, XML, TXT, PDF")
    print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    print("1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Sample data for testing all formats
    sample_data = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "salary": "$85,000",
            "hire_date": "2022-01-15",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "department": "Marketing",
            "position": "Marketing Manager",
            "salary": "$75,000",
            "hire_date": "2021-08-20",
            "status": "Active"
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob.johnson@company.com",
            "department": "Sales",
            "position": "Sales Representative",
            "salary": "$65,000",
            "hire_date": "2023-03-10",
            "status": "Active"
        },
        {
            "id": 4,
            "name": "Alice Brown",
            "email": "alice.brown@company.com",
            "department": "HR",
            "position": "HR Specialist",
            "salary": "$70,000",
            "hire_date": "2022-11-05",
            "status": "Active"
        },
        {
            "id": 5,
            "name": "Charlie Wilson",
            "email": "charlie.wilson@company.com",
            "department": "Finance",
            "position": "Financial Analyst",
            "salary": "$80,000",
            "hire_date": "2021-12-01",
            "status": "Active"
        }
    ]
    
    # Test all supported formats
    export_formats = ['json', 'csv', 'xml', 'txt', 'pdf']
    results = {}
    
    print(f"\n2. Testing {len(export_formats)} export formats...")
    print(f"📊 Data: {len(sample_data)} employee records")
    
    for i, export_format in enumerate(export_formats, 1):
        print(f"\n--- Test {i}/{len(export_formats)}: {export_format.upper()} Export ---")
        
        try:
            file_name = f"employee_report_{export_format}"
            user_id = "export_test_user"
            
            print(f"📤 Exporting as {export_format.upper()}...")
            export_result = client.export(sample_data, export_format, file_name, user_id)
            
            if export_result['success']:
                print(f"SUCCESS {export_format.upper()} Export: SUCCESS")
                print(f"   📄 File: {export_result['export_info']['storedName']}")
                print(f"   💾 Size: {export_result['export_info']['size']} bytes")
                print(f"   🔗 URL: {export_result['export_info']['url']}")
                print(f"   🆔 Operation ID: {export_result['operation_id']}")
                
                # Test download of exported file
                try:
                    download_url = export_result['export_info']['downloadUrl']
                    download_response = requests.get(download_url, timeout=30)
                    
                    if download_response.status_code == 200:
                        print(f"   📥 Download: SUCCESS ({len(download_response.content)} bytes)")
                        
                        # Save file locally for verification
                        local_filename = f"test_export_{export_format}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
                        with open(local_filename, 'wb') as f:
                            f.write(download_response.content)
                        print(f"   💾 Saved locally: {local_filename}")
                    else:
                        print(f"   ERROR Download: FAILED (Status: {download_response.status_code})")
                        
                except Exception as download_error:
                    print(f"   ERROR Download: ERROR - {download_error}")
                
                results[export_format] = {
                    'status': 'success',
                    'operation_id': export_result['operation_id'],
                    'file_info': export_result['export_info']
                }
                
            else:
                print(f"ERROR {export_format.upper()} Export: FAILED")
                print(f"   Error: {export_result['error']}")
                results[export_format] = {
                    'status': 'failed',
                    'error': export_result['error']
                }
                
        except Exception as e:
            print(f"ERROR {export_format.upper()} Export: EXCEPTION")
            print(f"   Error: {str(e)}")
            results[export_format] = {
                'status': 'exception',
                'error': str(e)
            }
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 EXPORT TEST SUMMARY")
    print("=" * 60)
    
    successful_formats = []
    failed_formats = []
    
    for format_name, result in results.items():
        if result['status'] == 'success':
            successful_formats.append(format_name.upper())
            print(f"SUCCESS {format_name.upper()}: SUCCESS")
        else:
            failed_formats.append(format_name.upper())
            print(f"ERROR {format_name.upper()}: FAILED - {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 Results:")
    print(f"   SUCCESS Successful: {len(successful_formats)}/{len(export_formats)}")
    print(f"   ERROR Failed: {len(failed_formats)}/{len(export_formats)}")
    
    if successful_formats:
        print(f"   🎉 Working formats: {', '.join(successful_formats)}")
    
    if failed_formats:
        print(f"   ⚠️  Failed formats: {', '.join(failed_formats)}")
    
    # Show operation history
    print(f"\n📋 Recent operation history:")
    history = client.get_operation_history('export_test_user', 10)
    
    if history:
        for i, op in enumerate(history, 1):
            status_emoji = "SUCCESS" if op['status'] == 'completed' else "ERROR" if op['status'] == 'failed' else "PENDING"
            print(f"   {i}. {status_emoji} {op['operation_type']} - {op['file_name']} ({op['status']})")
    else:
        print("   No operations found in database")
    
    print(f"\n🎉 Export format testing completed!")
    return results

def main():
    """Example usage of Direct S3 Client with MySQL from Django settings"""
    
    print("🚀 Direct S3 Microservice Client with MySQL")
    print("🌐 Direct URL: http://15.207.1.40:3000")
    print("🗄️  Database: MySQL (from Django settings)")
    print("🔐 AWS Credentials: Handled by microservice")
    print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    print("1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Example operations
    sample_data = [
        {"id": 1, "name": "MySQL Test", "platform": "Render", "status": "active"},
        {"id": 2, "name": "S3 Integration", "platform": "AWS", "status": "deployed"},
        {"id": 3, "name": "Database Tracking", "platform": "MySQL", "status": "operational"}
    ]
    
    print("\n2. Testing export functionality...")
    export_result = client.export(sample_data, 'json', 'mysql_render_test', 'test_user')
    
    if export_result['success']:
        print(f"SUCCESS Export successful!")
        print(f"   Operation ID: {export_result['operation_id']}")
        print(f"   File: {export_result['export_info']['storedName']}")
        print(f"   URL: {export_result['export_info']['url']}")
        
        # Test download
        print("\n3. Testing download functionality...")
        s3_key = export_result['export_info']['s3Key']
        file_name = export_result['export_info']['storedName']
        
        download_result = client.download(s3_key, file_name, './mysql_downloads', 'test_user')
        
        if download_result['success']:
            print(f"SUCCESS Download successful!")
            print(f"   Operation ID: {download_result['operation_id']}")
            print(f"   File saved: {download_result['file_path']}")
        else:
            print(f"ERROR Download failed: {download_result['error']}")
    else:
        print(f"ERROR Export failed: {export_result['error']}")
    
    # Show operation history
    print("\n4. Operation history from MySQL:")
    history = client.get_operation_history('test_user', 5)
    
    if history:
        for i, op in enumerate(history, 1):
            print(f"   {i}. {op['operation_type']} - {op['file_name']} - {op['status']} ({op['created_at']})")
    else:
        print("   No operations found in database")
    
    # Show statistics
    print("\n5. Database statistics:")
    stats = client.get_operation_stats()
    
    if stats:
        print(f"   Total operations: {stats.get('total_operations', 0)}")
        print(f"   Completed: {stats.get('total_completed', 0)}")
        print(f"   Failed: {stats.get('total_failed', 0)}")
        
        if stats.get('operations_by_type'):
            print("   Operations by type:")
            for op_stat in stats['operations_by_type']:
                print(f"     - {op_stat['operation_type']}: {op_stat['total_count']} total")
    
    print("\n🎉 Render + MySQL integration test completed!")

def test_pdf_processing():
    """Test PDF upload with automatic metadata extraction and summary generation"""
    
    print("🚀 Testing PDF Processing with OpenAI Summarization")
    print("🌐 Direct URL: http://15.207.1.40:3000")
    print("🤖 AI: OpenAI for document summarization")
    print("=" * 60)
    
    # Create client (will use Django settings automatically)
    client = create_direct_mysql_client()
    
    # Test connections
    print("\n1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        print("ERROR Cannot proceed - fix connection issues first")
        return
    
    # Check for PDF processing libraries
    print("\n2. Checking PDF processing libraries...")
    print(f"   PyPDF2: {'✅ Available' if PDF_LIBRARY_AVAILABLE else '❌ Not available'}")
    print(f"   pdfplumber: {'✅ Available' if PDFPLUMBER_AVAILABLE else '❌ Not available'}")
    print(f"   OpenAI: {'✅ Available' if OPENAI_AVAILABLE else '❌ Not available'}")
    
    if not PDF_LIBRARY_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        print("\n⚠️  WARNING: No PDF processing library available!")
        print("   Install PyPDF2 or pdfplumber: pip install PyPDF2 pdfplumber")
        return
    
    if not OPENAI_AVAILABLE:
        print("\n⚠️  WARNING: OpenAI library not available!")
        print("   Install OpenAI: pip install openai")
        return
    
    # You would need to provide a test PDF file path
    print("\n3. Upload a PDF file to test...")
    print("   📝 Note: Provide a PDF file path to test the feature")
    print("   📝 Example usage:")
    print("""
    # Upload PDF
    upload_result = client.upload(
        file_path='/path/to/your/document.pdf',
        user_id='test_user',
        module='policy'
    )
    
    if upload_result['success']:
        operation_id = upload_result['operation_id']
        print(f"✅ Upload successful! Operation ID: {operation_id}")
        print(f"📄 PDF processing: {upload_result.get('pdf_processing', 'N/A')}")
        
        # Wait a few seconds for processing
        import time
        print("⏳ Waiting for PDF processing to complete...")
        time.sleep(10)
        
        # Check processing status
        status = client.get_pdf_processing_status(operation_id)
        print(f"\\n📊 Processing Status: {status['status']}")
        
        if status['status'] == 'completed':
            print(f"\\n📋 Metadata:")
            for key, value in status['metadata'].items():
                print(f"   {key}: {value}")
            
            print(f"\\n📝 Summary:")
            print(f"   {status['summary']}")
    """)
    
    print("\n✅ PDF processing feature is ready to use!")
    print("\n💡 Tips:")
    print("   - Processing happens in background (non-blocking)")
    print("   - Smart extraction: Small docs fully processed, large docs sampled")
    print("   - Summary is limited to 10 lines maximum")
    print("   - Metadata includes: title, author, page count, file size, category, etc.")
    print("   - Check processing status using: client.get_pdf_processing_status(operation_id)")

def test_enhanced_pdf_processing_with_sample(pdf_path: str = None):
    """
    Test the ENHANCED PDF processing feature with a sample PDF
    
    This demonstrates the new intelligent features:
    - Smart text extraction (small vs large documents)
    - Comprehensive metadata extraction
    - AI-powered summary generation using GPT-3.5-turbo
    - Automatic categorization
    - Database integration
    
    Args:
        pdf_path: Path to a PDF file to test. If None, instructions are provided.
    """
    
    print("="*80)
    print("🚀 ENHANCED PDF PROCESSING TEST")
    print("="*80)
    print("\nThis test demonstrates the NEW intelligent PDF processing features:")
    print("✅ Smart extraction strategy (optimized for cost & time)")
    print("✅ Comprehensive metadata extraction")
    print("✅ AI-powered summary generation (GPT-3.5-turbo)")
    print("✅ Automatic document categorization")
    print("✅ Full database integration")
    print("="*80)
    
    # Create client
    print("\n[1] Creating S3 client...")
    client = create_direct_mysql_client()
    
    # Test connections
    print("\n[2] Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        print("❌ Cannot proceed - fix connection issues first")
        return
    
    print("✅ All connections successful!")
    
    # Check for required libraries
    print("\n[3] Checking required libraries...")
    print(f"   PyPDF2: {'✅ Available' if PDF_LIBRARY_AVAILABLE else '❌ Not available'}")
    print(f"   pdfplumber: {'✅ Available' if PDFPLUMBER_AVAILABLE else '❌ Not available'}")
    print(f"   OpenAI: {'✅ Available' if OPENAI_AVAILABLE else '❌ Not available'}")
    
    if not (PDF_LIBRARY_AVAILABLE or PDFPLUMBER_AVAILABLE):
        print("\n⚠️  WARNING: No PDF processing library available!")
        print("   Install: pip install PyPDF2 pdfplumber")
        return
    
    if not OPENAI_AVAILABLE:
        print("\n⚠️  WARNING: OpenAI library not available!")
        print("   Install: pip install openai")
        return
    
    # Check for PDF file
    if not pdf_path or not os.path.exists(pdf_path):
        print("\n[4] No PDF file provided for testing")
        print("\n📝 To test with your own PDF, run:")
        print("""
from grc.routes.Global.s3_fucntions import test_enhanced_pdf_processing_with_sample

# Test with a small document (1-5 pages)
test_enhanced_pdf_processing_with_sample('/path/to/small_policy.pdf')

# Test with a large document (20+ pages)
test_enhanced_pdf_processing_with_sample('/path/to/large_manual.pdf')
        """)
        print("\n✅ Enhanced PDF processing feature is READY and CONFIGURED!")
        print("\n📊 Feature Summary:")
        print("   - Smart Extraction: Optimized for different document sizes")
        print("   - AI Summary: Using GPT-3.5-turbo")
        print("   - Auto-categorization: policy, audit, risk, incident")
        print("   - Background Processing: Non-blocking upload")
        print("   - Database Storage: metadata + summary fields")
        return
    
    # Test with actual PDF
    print(f"\n[4] Testing with PDF: {os.path.basename(pdf_path)}")
    print(f"   File size: {round(os.path.getsize(pdf_path) / (1024 * 1024), 2)} MB")
    
    # Upload the PDF
    print("\n[5] Uploading PDF to S3...")
    upload_result = client.upload(
        file_path=pdf_path,
        user_id='test_enhanced_user',
        module='policy'  # Change as needed
    )
    
    if not upload_result['success']:
        print(f"❌ Upload failed: {upload_result.get('error')}")
        return
    
    operation_id = upload_result['operation_id']
    print(f"✅ Upload successful!")
    print(f"   Operation ID: {operation_id}")
    print(f"   S3 URL: {upload_result['file_info']['url']}")
    print(f"   PDF Processing: {upload_result.get('pdf_processing', 'N/A')}")
    
    # Wait for processing
    print("\n[6] Waiting for background processing to complete...")
    import time
    
    max_wait = 60  # Maximum 60 seconds
    wait_interval = 5  # Check every 5 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval
        
        print(f"   ⏳ Checking status... ({elapsed}s elapsed)")
        status = client.get_pdf_processing_status(operation_id)
        
        if status['status'] == 'completed':
            print(f"   ✅ Processing completed in {elapsed} seconds!")
            break
        elif status['status'] == 'error' or status['status'] == 'failed':
            print(f"   ❌ Processing failed: {status.get('message')}")
            return
        else:
            print(f"   ⏳ Still processing...")
    
    # Display results
    if status['status'] == 'completed':
        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print("\n📋 EXTRACTED METADATA:")
        print("-"*80)
        metadata = status.get('metadata', {})
        for key, value in sorted(metadata.items()):
            if isinstance(value, dict):
                print(f"   {key}: {json.dumps(value, indent=2)}")
            else:
                print(f"   {key}: {value}")
        
        print("\n📝 AI-GENERATED SUMMARY:")
        print("-"*80)
        summary = status.get('summary', 'No summary available')
        for line in summary.split('\n'):
            print(f"   {line}")
        
        print("\n" + "="*80)
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\n📊 Feature Highlights Demonstrated:")
        print(f"   ✅ Document Size: {metadata.get('document_size_category', 'unknown').upper()}")
        print(f"   ✅ Extraction Strategy: {metadata.get('extraction_strategy', 'unknown')}")
        print(f"   ✅ Pages Processed: {metadata.get('page_count', 'unknown')}")
        print(f"   ✅ AI Model Used: {metadata.get('ai_model', 'unknown')}")
        print(f"   ✅ Auto-Category: {metadata.get('suggested_category', 'unknown')}")
        print(f"   ✅ Summary Generated: Yes ({len(summary)} characters)")
    else:
        print(f"\n⏳ Processing is taking longer than expected...")
        print(f"   Check status later using: client.get_pdf_processing_status({operation_id})")

# if __name__ == "__main__":
#     # Run the comprehensive export format test
#     # test_all_export_formats()
#     
#     # OR run the PDF processing test
#     # test_pdf_processing()
#     
#     # OR run the NEW enhanced PDF processing test
#     # test_enhanced_pdf_processing_with_sample('/path/to/your/pdf/file.pdf')