"""Response compression middleware for performance optimization."""

import gzip
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to compress responses for better performance."""
    
    # Minimum size for compression (1KB)
    MIN_SIZE = 1024
    
    # Content types to compress
    COMPRESSIBLE_TYPES = {
        "application/json",
        "text/html",
        "text/css",
        "text/javascript",
        "application/javascript",
        "text/plain",
        "text/xml",
        "application/xml",
        "application/geo+json",
    }
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 1024,
        compression_level: int = 6
    ):
        """Initialize compression middleware.
        
        Args:
            app: ASGI application
            minimum_size: Minimum response size to compress
            compression_level: gzip compression level (1-9)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and compress response if applicable."""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return await call_next(request)
        
        # Process request
        response = await call_next(request)
        
        # Check if response should be compressed
        if not self._should_compress(response):
            return response
        
        # For streaming responses, wrap with compression
        if isinstance(response, StreamingResponse):
            return await self._compress_streaming_response(response, request)
        
        # For regular responses, compress body
        return await self._compress_response(response)
    
    def _should_compress(self, response: Response) -> bool:
        """Check if response should be compressed.
        
        Args:
            response: Response object
            
        Returns:
            True if response should be compressed
        """
        # Don't compress if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        base_type = content_type.split(";")[0].strip().lower()
        
        if base_type not in self.COMPRESSIBLE_TYPES:
            return False
        
        # Check content length if available
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def _compress_response(self, response: Response) -> Response:
        """Compress a regular response.
        
        Args:
            response: Response to compress
            
        Returns:
            Compressed response
        """
        try:
            # Read response body
            body = response.body
            
            # Check size
            if len(body) < self.minimum_size:
                return response
            
            # Compress body
            compressed = gzip.compress(body, compresslevel=self.compression_level)
            
            # Update response
            response.body = compressed
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed))
            
            # Add vary header
            vary = response.headers.get("vary", "")
            if vary:
                response.headers["vary"] = f"{vary}, Accept-Encoding"
            else:
                response.headers["vary"] = "Accept-Encoding"
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to compress response: {e}")
            return response
    
    async def _compress_streaming_response(
        self,
        response: StreamingResponse,
        request: Request
    ) -> StreamingResponse:
        """Compress a streaming response.
        
        Args:
            response: Streaming response to compress
            request: Original request
            
        Returns:
            Compressed streaming response
        """
        try:
            # Create compressed stream generator
            async def compressed_stream():
                compressor = gzip.GzipFile(
                    mode="wb",
                    compresslevel=self.compression_level
                )
                
                async for chunk in response.body_iterator:
                    if chunk:
                        compressed_chunk = compressor.compress(chunk)
                        if compressed_chunk:
                            yield compressed_chunk
                
                # Flush remaining data
                final = compressor.flush()
                if final:
                    yield final
            
            # Create new streaming response with compression
            compressed_response = StreamingResponse(
                compressed_stream(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # Update headers
            compressed_response.headers["content-encoding"] = "gzip"
            
            # Remove content-length as it's unknown for streaming
            compressed_response.headers.pop("content-length", None)
            
            # Add vary header
            vary = compressed_response.headers.get("vary", "")
            if vary:
                compressed_response.headers["vary"] = f"{vary}, Accept-Encoding"
            else:
                compressed_response.headers["vary"] = "Accept-Encoding"
            
            return compressed_response
            
        except Exception as e:
            logger.error(f"Failed to compress streaming response: {e}")
            return response


def setup_compression(
    app: FastAPI,
    minimum_size: int = 1024,
    compression_level: int = 6
):
    """Set up response compression middleware.
    
    Args:
        app: FastAPI application
        minimum_size: Minimum response size to compress
        compression_level: gzip compression level (1-9)
    """
    app.add_middleware(
        CompressionMiddleware,
        minimum_size=minimum_size,
        compression_level=compression_level
    )
    
    logger.info(f"Response compression enabled (min_size={minimum_size}, level={compression_level})")