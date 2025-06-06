"""
Unit tests for ThumbnailCache service.
"""
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

import pytest
from PySide6.QtGui import QPixmap

from slideman.services.thumbnail_cache import ThumbnailCache


class TestThumbnailCache:
    """Test suite for ThumbnailCache service."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_path = tmp_path / "thumbnails"
        cache_path.mkdir()
        return cache_path

    @pytest.fixture
    def cache(self, cache_dir):
        """Create ThumbnailCache instance with temp directory."""
        # Reset singleton
        ThumbnailCache._instance = None
        
        with patch('slideman.services.thumbnail_cache.ThumbnailCache._get_cache_directory') as mock_dir:
            mock_dir.return_value = cache_dir
            cache = ThumbnailCache()
            yield cache
            # Cleanup
            cache.clear_cache()

    @pytest.fixture
    def sample_thumbnail(self, cache_dir):
        """Create a sample thumbnail file."""
        thumb_path = cache_dir / "test_thumb.png"
        # Create a simple image file (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        thumb_path.write_bytes(png_data)
        return str(thumb_path)

    def test_singleton_pattern(self, cache_dir):
        """Test that ThumbnailCache follows singleton pattern."""
        with patch('slideman.services.thumbnail_cache.ThumbnailCache._get_cache_directory') as mock_dir:
            mock_dir.return_value = cache_dir
            
            cache1 = ThumbnailCache()
            cache2 = ThumbnailCache()
            
            assert cache1 is cache2

    def test_initialization(self, cache):
        """Test cache initialization."""
        assert cache._memory_cache == {}
        assert cache._cache_info == {}
        assert cache._max_memory_size == 100 * 1024 * 1024  # 100MB
        assert cache._current_memory_usage == 0

    def test_get_cache_directory_windows(self):
        """Test cache directory on Windows."""
        ThumbnailCache._instance = None
        
        with patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'}):
            with patch('slideman.services.thumbnail_cache.ThumbnailCache.__init__', return_value=None):
                cache = ThumbnailCache()
                result = cache._get_cache_directory()
                assert result == Path('C:\\Users\\Test\\AppData\\Local\\SlideMan\\thumbnails')

    def test_get_cache_directory_unix(self):
        """Test cache directory on Unix systems."""
        ThumbnailCache._instance = None
        
        with patch.dict(os.environ, {'HOME': '/home/test'}, clear=True):
            os.environ.pop('LOCALAPPDATA', None)
            with patch('slideman.services.thumbnail_cache.ThumbnailCache.__init__', return_value=None):
                cache = ThumbnailCache()
                result = cache._get_cache_directory()
                assert result == Path('/home/test/.cache/slideman/thumbnails')

    def test_get_thumbnail_from_disk(self, cache, sample_thumbnail):
        """Test getting thumbnail that exists on disk."""
        slide_id = 123
        
        # Create cache file with expected name
        cache_path = Path(cache._cache_dir) / f"slide_{slide_id}.png"
        import shutil
        shutil.copy(sample_thumbnail, cache_path)
        
        result = cache.get_thumbnail(slide_id, sample_thumbnail)
        
        assert result == str(cache_path)
        assert slide_id in cache._memory_cache
        assert cache._current_memory_usage > 0

    def test_get_thumbnail_from_memory(self, cache):
        """Test getting thumbnail from memory cache."""
        slide_id = 123
        cached_path = "/cached/thumb.png"
        
        # Pre-populate memory cache
        cache._memory_cache[slide_id] = cached_path
        cache._cache_info[slide_id] = {
            'size': 1024,
            'last_access': time.time()
        }
        
        result = cache.get_thumbnail(slide_id, "/original/thumb.png")
        
        assert result == cached_path
        # Should update last access time
        assert cache._cache_info[slide_id]['last_access'] > 0

    def test_get_thumbnail_copy_to_cache(self, cache, sample_thumbnail):
        """Test copying thumbnail to cache when not cached."""
        slide_id = 123
        
        result = cache.get_thumbnail(slide_id, sample_thumbnail)
        
        expected_cache_path = cache._cache_dir / f"slide_{slide_id}.png"
        assert result == str(expected_cache_path)
        assert expected_cache_path.exists()
        assert slide_id in cache._memory_cache

    def test_get_thumbnail_source_not_found(self, cache):
        """Test getting thumbnail when source doesn't exist."""
        slide_id = 123
        
        with patch.object(cache, '_get_placeholder_thumbnail') as mock_placeholder:
            mock_placeholder.return_value = "/placeholder.png"
            
            result = cache.get_thumbnail(slide_id, "/nonexistent/thumb.png")
            
            assert result == "/placeholder.png"
            mock_placeholder.assert_called_once()

    def test_has_thumbnail_in_memory(self, cache):
        """Test checking if thumbnail exists in memory."""
        slide_id = 123
        cache._memory_cache[slide_id] = "/cached/thumb.png"
        
        assert cache.has_thumbnail(slide_id) is True

    def test_has_thumbnail_on_disk(self, cache):
        """Test checking if thumbnail exists on disk."""
        slide_id = 123
        cache_path = cache._cache_dir / f"slide_{slide_id}.png"
        cache_path.touch()
        
        assert cache.has_thumbnail(slide_id) is True

    def test_has_thumbnail_not_exists(self, cache):
        """Test checking non-existent thumbnail."""
        assert cache.has_thumbnail(999) is False

    def test_remove_thumbnail(self, cache, sample_thumbnail):
        """Test removing thumbnail from cache."""
        slide_id = 123
        
        # Add to cache first
        cache.get_thumbnail(slide_id, sample_thumbnail)
        assert cache.has_thumbnail(slide_id)
        
        # Remove
        cache.remove_thumbnail(slide_id)
        
        assert slide_id not in cache._memory_cache
        assert slide_id not in cache._cache_info
        cache_path = cache._cache_dir / f"slide_{slide_id}.png"
        assert not cache_path.exists()

    def test_clear_cache(self, cache, sample_thumbnail):
        """Test clearing entire cache."""
        # Add multiple thumbnails
        for i in range(3):
            cache.get_thumbnail(i, sample_thumbnail)
        
        assert len(cache._memory_cache) == 3
        
        cache.clear_cache()
        
        assert len(cache._memory_cache) == 0
        assert len(cache._cache_info) == 0
        assert cache._current_memory_usage == 0
        
        # Check disk cache is cleared
        assert len(list(cache._cache_dir.glob("*.png"))) == 0

    def test_memory_eviction_lru(self, cache, sample_thumbnail):
        """Test LRU eviction when memory limit exceeded."""
        # Set small memory limit
        cache._max_memory_size = 5000  # 5KB
        
        # Add thumbnails until eviction occurs
        for i in range(10):
            cache.get_thumbnail(i, sample_thumbnail)
            time.sleep(0.01)  # Ensure different access times
        
        # Should have evicted oldest entries
        assert len(cache._memory_cache) < 10
        assert cache._current_memory_usage <= cache._max_memory_size
        
        # Newest entries should still be in cache
        assert 9 in cache._memory_cache
        assert 8 in cache._memory_cache

    def test_get_placeholder_thumbnail(self, cache):
        """Test getting placeholder thumbnail."""
        with patch('slideman.services.thumbnail_cache.QPixmap') as mock_pixmap:
            mock_pixmap_instance = MagicMock()
            mock_pixmap_instance.save.return_value = True
            mock_pixmap.return_value = mock_pixmap_instance
            
            result = cache._get_placeholder_thumbnail()
            
            assert "placeholder" in result
            mock_pixmap.assert_called_once_with(160, 120)
            mock_pixmap_instance.fill.assert_called_once()
            mock_pixmap_instance.save.assert_called_once()

    def test_estimate_pixmap_size(self, cache):
        """Test estimating QPixmap memory size."""
        pixmap = QPixmap(100, 100)
        
        # Size should be width * height * 4 bytes (RGBA)
        size = cache._estimate_pixmap_size(pixmap)
        assert size == 100 * 100 * 4

    def test_cache_persistence(self, cache, sample_thumbnail):
        """Test that disk cache persists between instances."""
        slide_id = 123
        
        # Add to cache
        result1 = cache.get_thumbnail(slide_id, sample_thumbnail)
        
        # Create new instance (simulate app restart)
        ThumbnailCache._instance = None
        new_cache = ThumbnailCache()
        
        # Should find existing cached file
        assert new_cache.has_thumbnail(slide_id)
        result2 = new_cache.get_thumbnail(slide_id, "/different/source.png")
        assert result1 == result2

    def test_concurrent_access(self, cache, sample_thumbnail):
        """Test cache handles concurrent access safely."""
        from concurrent.futures import ThreadPoolExecutor
        
        def access_cache(slide_id):
            return cache.get_thumbnail(slide_id, sample_thumbnail)
        
        # Multiple threads accessing same thumbnail
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(access_cache, 123) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All should get same result
        assert all(r == results[0] for r in results)
        assert cache._memory_cache[123] == results[0]

    def test_get_cache_statistics(self, cache, sample_thumbnail):
        """Test getting cache statistics."""
        # Add some thumbnails
        for i in range(5):
            cache.get_thumbnail(i, sample_thumbnail)
        
        stats = cache.get_cache_statistics()
        
        assert stats['memory_cache_count'] == 5
        assert stats['memory_usage'] > 0
        assert stats['memory_usage'] <= cache._max_memory_size
        assert stats['max_memory_size'] == cache._max_memory_size
        assert stats['disk_cache_count'] >= 5

    def test_invalidate_project_thumbnails(self, cache, sample_thumbnail):
        """Test invalidating thumbnails for a project."""
        # Add thumbnails for multiple projects
        project_slides = {1: [1, 2, 3], 2: [4, 5, 6]}
        
        for project_id, slide_ids in project_slides.items():
            for slide_id in slide_ids:
                cache.get_thumbnail(slide_id, sample_thumbnail)
        
        # Invalidate project 1
        cache.invalidate_project_thumbnails(project_slides[1])
        
        # Project 1 thumbnails should be gone
        for slide_id in project_slides[1]:
            assert not cache.has_thumbnail(slide_id)
        
        # Project 2 thumbnails should remain
        for slide_id in project_slides[2]:
            assert cache.has_thumbnail(slide_id)