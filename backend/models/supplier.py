from typing import Any

from pydantic import BaseModel


class FtpFileConfig(BaseModel):
    path: str
    role: str = "products"
    label: str | None = None
    separator: str | None = ";"
    header_row: int | None = 1
    merge_key: str | None = None


class SupplierCreate(BaseModel):
    name: str
    description: str | None = None
    connection_type: str | None = "ftp"
    file_url: str | None = None
    url_username: str | None = None
    url_password: str | None = None
    ftp_schema: str | None = "ftp"
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_password: str | None = None
    ftp_port: int | None = 21
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = "passive"
    file_format: str | None = "csv"
    csv_separator: str | None = ";"
    csv_enclosure: str | None = '"'
    csv_line_break: str | None = "\\n"
    csv_header_row: int | None = 1
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = False
    preset_id: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    connection_type: str | None = None
    file_url: str | None = None
    url_username: str | None = None
    url_password: str | None = None
    ftp_schema: str | None = None
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_password: str | None = None
    ftp_port: int | None = None
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = None
    file_format: str | None = None
    csv_separator: str | None = None
    csv_enclosure: str | None = None
    csv_line_break: str | None = None
    csv_header_row: int | None = None
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = None
    preset_id: str | None = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    connection_type: str | None = "ftp"
    file_url: str | None = None
    url_username: str | None = None
    ftp_schema: str | None = None
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_port: int | None = None
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = None
    file_format: str | None = None
    csv_separator: str | None = None
    csv_enclosure: str | None = None
    csv_line_break: str | None = None
    csv_header_row: int | None = None
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = False
    preset_id: str | None = None
    detected_columns: Any | None = None  # Puede ser List[str] o Dict[str, List[str]] para multi-archivo
    product_count: int = 0
    last_sync: str | None = None
    created_at: str
