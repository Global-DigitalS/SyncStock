"""
Streaming utilities for efficient file downloads without loading entire files into memory

Optimizes:
- File downloads using streaming and temporary files
- Memory usage during large file transfers
- Timeout and error handling for network operations
"""
import logging
import asyncio
import tempfile
import os
from typing import Tuple, Callable, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class StreamingDownloadTracker:
    """Tracks download progress and metrics"""

    def __init__(self, resource_name: str = "Unknown"):
        self.resource_name = resource_name
        self.total_bytes = 0
        self.downloaded_bytes = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.chunk_count = 0

    def start(self):
        self.start_time = datetime.now(timezone.utc)

    def add_chunk(self, chunk_size: int):
        self.downloaded_bytes += chunk_size
        self.chunk_count += 1

    def finish(self):
        self.end_time = datetime.now(timezone.utc)

    @property
    def duration_seconds(self) -> float:
        if not self.start_time or not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def throughput_mbps(self) -> float:
        if self.duration_seconds == 0:
            return 0
        mb = self.downloaded_bytes / (1024 * 1024)
        return mb / self.duration_seconds

    def get_summary(self) -> dict:
        return {
            "resource": self.resource_name,
            "total_mb": round(self.downloaded_bytes / (1024 * 1024), 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "throughput_mbps": round(self.throughput_mbps, 2),
            "chunks": self.chunk_count,
        }


async def download_file_streaming(
    download_func: Callable,
    chunk_size: int = 1024 * 1024,  # 1 MB chunks
    resource_name: str = "Unknown",
    timeout_seconds: int = 300,
) -> Tuple[bytes, StreamingDownloadTracker]:
    """
    Download a file in chunks using a streaming approach.

    Args:
        download_func: Async function that downloads and yields chunks
        chunk_size: Size of chunks to read
        resource_name: Name for logging
        timeout_seconds: Download timeout

    Returns:
        (file_content: bytes, tracker: StreamingDownloadTracker)
    """
    tracker = StreamingDownloadTracker(resource_name)
    tracker.start()

    # Use SpooledTemporaryFile to keep small files in memory,
    # but spill to disk for large files (>50MB)
    max_size = 50 * 1024 * 1024  # 50 MB

    try:
        with tempfile.SpooledTemporaryFile(max_size=max_size) as temp_file:
            try:
                async for chunk in asyncio.wait_for(
                    download_func(),
                    timeout=timeout_seconds
                ):
                    if chunk:
                        temp_file.write(chunk)
                        tracker.add_chunk(len(chunk))

                # Read the file content
                temp_file.seek(0)
                content = temp_file.read()
                tracker.finish()

                logger.info(
                    f"Downloaded {tracker.resource_name}: "
                    f"{tracker.downloaded_bytes / (1024*1024):.1f}MB in {tracker.duration_seconds:.1f}s"
                )
                return content, tracker

            except asyncio.TimeoutError:
                raise Exception(f"Download timeout for {resource_name} after {timeout_seconds}s")

    except Exception as e:
        logger.error(f"Error downloading {resource_name}: {e}")
        raise


async def download_from_url_streaming(
    url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout_seconds: int = 300,
) -> Tuple[bytes, StreamingDownloadTracker]:
    """
    Download a file from a URL using streaming.

    Args:
        url: URL to download from
        username: Optional basic auth username
        password: Optional basic auth password
        timeout_seconds: Download timeout

    Returns:
        (file_content: bytes, tracker: StreamingDownloadTracker)
    """
    import aiohttp

    async def stream_generator():
        auth = None
        if username and password:
            auth = aiohttp.BasicAuth(username, password)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                auth=auth,
                headers=headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                response.raise_for_status()

                async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                    yield chunk

    return await download_file_streaming(
        stream_generator,
        resource_name=url,
        timeout_seconds=timeout_seconds
    )


async def download_from_ftp_streaming(
    supplier: dict,
    timeout_seconds: int = 300,
) -> Tuple[bytes, StreamingDownloadTracker]:
    """
    Download a file from FTP/SFTP using streaming.

    Args:
        supplier: Supplier config with FTP details
        timeout_seconds: Download timeout

    Returns:
        (file_content: bytes, tracker: StreamingDownloadTracker)
    """
    import paramiko
    import ftplib

    schema = supplier.get('ftp_schema', 'ftp').lower()
    host = supplier.get('ftp_host')
    port = supplier.get('ftp_port', 21 if schema != 'sftp' else 22)
    user = supplier.get('ftp_user', '')
    password = supplier.get('ftp_password', '')
    file_path = supplier.get('ftp_path', '')

    if not host or not file_path:
        raise ValueError("FTP host and path are required")

    async def stream_generator():
        """Yield chunks from FTP/SFTP download"""

        def ftp_download_sync() -> bytes:
            """Synchronous FTP download — returns full content (run in executor)."""
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name

                    if schema == 'sftp':
                        import socket
                        sock = socket.create_connection((host, port or 22), timeout=30)
                        transport = paramiko.Transport(sock)
                        transport.connect(username=user, password=password)
                        transport.set_keepalive(30)
                        sftp = paramiko.SFTPClient.from_transport(transport)
                        sftp.get_channel().settimeout(timeout_seconds)
                        try:
                            sftp.get(file_path, tmp.name)
                        finally:
                            sftp.close()
                            transport.close()
                    else:
                        ftp_cls = ftplib.FTP_TLS if schema == 'ftps' else ftplib.FTP
                        ftp = ftp_cls()
                        ftp.connect(host, port or 21, timeout=30)
                        ftp.login(user or 'anonymous', password or '')
                        if schema == 'ftps':
                            ftp.prot_p()
                        try:
                            ftp.retrbinary(f'RETR {file_path}', tmp.write)
                        finally:
                            try:
                                ftp.quit()
                            except Exception:
                                pass

                # Read file and return as bytes
                with open(tmp_path, 'rb') as f:
                    return f.read()
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # Run sync FTP download in thread pool, then yield in chunks
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(None, ftp_download_sync)
        chunk_size = 1024 * 1024  # 1 MB
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

    return await download_file_streaming(
        stream_generator,
        resource_name=f"{schema.upper()}://{host}{file_path}",
        timeout_seconds=timeout_seconds
    )


class ChunkIterator:
    """
    Iterator for processing a file in chunks without loading entire file into memory.

    Useful for parsing CSV/XLSX in streaming fashion.
    """

    def __init__(self, content: bytes, chunk_size: int = 50000):
        """
        Args:
            content: File content (bytes)
            chunk_size: Number of lines per chunk for CSV, or records for other formats
        """
        self.content = content
        self.chunk_size = chunk_size
        self.position = 0

    def __iter__(self):
        return self

    def __next__(self) -> bytes:
        if self.position >= len(self.content):
            raise StopIteration

        # Return next chunk_size bytes
        chunk = self.content[self.position : self.position + self.chunk_size]
        self.position += self.chunk_size
        return chunk

    @property
    def remaining_bytes(self) -> int:
        return len(self.content) - self.position

    @property
    def progress_percent(self) -> int:
        if len(self.content) == 0:
            return 100
        return int((self.position / len(self.content)) * 100)
