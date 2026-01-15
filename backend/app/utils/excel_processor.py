import pandas as pd
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Process and parse Excel BOQ files"""
    
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls']
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def read_excel(self, file_path: str, sheet_name: int = 0) -> pd.DataFrame:
        """Read Excel file into DataFrame"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully read Excel file: {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def detect_header_row(self, df: pd.DataFrame, max_rows_to_check: int = 10) -> int:
        """
        Detect the header row by finding the row with maximum non-null values
        """
        header_row = 0
        max_non_null = 0
        
        for i in range(min(max_rows_to_check, len(df))):
            non_null_count = df.iloc[i].notna().sum()
            if non_null_count > max_non_null:
                max_non_null = non_null_count
                header_row = i
        
        logger.info(f"Detected header row at index: {header_row}")
        return header_row
    
    def detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Auto-detect column mapping based on common keywords
        Returns mapping: {original_column: standard_column}
        """
        mapping = {}
        
        # Keywords for each standard column
        keywords_map = {
            'description': ['description', 'mô tả', 'hạng mục', 'item', 'work item', 'nội dung'],
            'unit': ['unit', 'đơn vị', 'đvt', 'uom'],
            'quantity': ['quantity', 'số lượng', 'qty', 'khối lượng', 'volume'],
            'unit_price': ['unit price', 'đơn giá', 'rate', 'price', 'giá'],
            'amount': ['amount', 'thành tiền', 'total', 'value', 'tổng']
        }
        
        for col in columns:
            col_lower = str(col).lower().strip()
            
            for standard_name, keywords in keywords_map.items():
                if any(keyword in col_lower for keyword in keywords):
                    mapping[col] = standard_name
                    break
        
        logger.info(f"Detected column mapping: {mapping}")
        return mapping
    
    def parse_structure(self, file_path: str) -> Dict:
        """
        Analyze Excel file structure and return metadata
        """
        df = self.read_excel(file_path)
        
        # Detect header row
        header_row = self.detect_header_row(df)
        
        # Set header and clean data
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        df = df.dropna(how='all')  # Remove completely empty rows
        
        # Detect columns
        column_mapping = self.detect_columns(df.columns.tolist())
        
        # Generate preview
        preview_data = df.head(10).to_dict('records')
        
        return {
            'header_row': header_row,
            'total_rows': len(df),
            'columns': df.columns.tolist(),
            'column_mapping': column_mapping,
            'preview': preview_data,
            'detected_columns': list(column_mapping.values())
        }
    
    def clean_data(
        self,
        df: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Clean and standardize DataFrame data
        """
        # Rename columns according to mapping
        df = df.rename(columns=column_mapping)
        
        # Remove rows without description
        if 'description' in df.columns:
            df = df.dropna(subset=['description'])
            df = df[df['description'].astype(str).str.strip() != '']
        
        # Clean description
        if 'description' in df.columns:
            df['description'] = df['description'].astype(str).str.strip()
        
        # Standardize units
        if 'unit' in df.columns:
            df['unit'] = df['unit'].apply(self._standardize_unit)
        
        # Convert numeric columns
        numeric_columns = ['quantity', 'unit_price', 'amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate amount if not present
        if 'amount' not in df.columns and 'quantity' in df.columns and 'unit_price' in df.columns:
            df['amount'] = df['quantity'] * df['unit_price']
        
        # Filter out zero quantity items
        if 'quantity' in df.columns:
            df = df[df['quantity'] > 0]
        
        # Reset index
        df = df.reset_index(drop=True)
        
        logger.info(f"Cleaned data: {len(df)} rows remaining")
        return df
    
    def _standardize_unit(self, unit: any) -> str:
        """
        Standardize unit values to common formats
        """
        if pd.isna(unit):
            return 'pcs'
        
        unit_str = str(unit).lower().strip()
        
        # Unit mapping dictionary
        unit_map = {
            'm': ['m', 'met', 'meter', 'mét'],
            'm2': ['m2', 'm²', 'sqm', 'sq.m', 'square meter'],
            'm3': ['m3', 'm³', 'cbm', 'cubic meter', 'khối'],
            'kg': ['kg', 'kilo', 'kilogram'],
            'ton': ['ton', 'tấn', 't', 'tonne'],
            'pcs': ['pcs', 'pc', 'cái', 'chiếc', 'ea', 'each', 'piece'],
            'set': ['set', 'bộ'],
            'lot': ['lot', 'lô'],
            'ml': ['ml', 'liter', 'lít', 'l'],
            'day': ['day', 'ngày', 'd'],
            'hour': ['hour', 'giờ', 'hr', 'h'],
        }
        
        for standard, variations in unit_map.items():
            if unit_str in variations:
                return standard
        
        # If no match found, return original (cleaned)
        return unit_str[:10]  # Limit length
    
    def extract_line_items(
        self,
        df: pd.DataFrame,
        file_id: int,
        project_id: int
    ) -> List[Dict]:
        """
        Extract line items from cleaned DataFrame
        """
        line_items = []
        
        for idx, row in df.iterrows():
            item = {
                'file_id': file_id,
                'project_id': project_id,
                'row_number': idx + 1,
                'description': row.get('description', ''),
                'unit': row.get('unit', 'pcs'),
                'quantity': float(row.get('quantity', 0)),
                'unit_price': float(row.get('unit_price', 0)),
                'amount': float(row.get('amount', 0)),
            }
            line_items.append(item)
        
        logger.info(f"Extracted {len(line_items)} line items")
        return line_items
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Excel file
        Returns: (is_valid, error_message)
        """
        file_path_obj = Path(file_path)
        
        # Check if file exists
        if not file_path_obj.exists():
            return False, "File does not exist"
        
        # Check extension
        if file_path_obj.suffix.lower() not in self.supported_extensions:
            return False, f"Unsupported file type. Allowed: {', '.join(self.supported_extensions)}"
        
        # Try to read file
        try:
            df = pd.read_excel(file_path)
            if df.empty:
                return False, "File is empty"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"
        
        return True, None
